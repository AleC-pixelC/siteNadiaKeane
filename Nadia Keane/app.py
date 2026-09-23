import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chave_secreta_nadia_keane"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bancoNK.db')

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def conectar_bd():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"A base de dados não foi encontrada em '{DB_PATH}'."
        )
    
    conexao = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True)
    conexao.row_factory = sqlite3.Row
    return conexao


def login_necessario(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para fazer isso.')
            return redirect(url_for('login', proxima=request.path))
        return f(*args, **kwargs)
    return decorada


@app.context_processor
def injetar_usuario():
    return dict(usuario_logado=session.get('usuario_nome'))


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/inicio')
def pagina_principal():
    return render_template('paginaPrincipal.html')


@app.route('/autora')
def autora():
    return render_template('autora.html')


@app.route('/personagens')
def personagens():
    return render_template('personagens.html')


@app.route('/historia')
def historia():
    return render_template('historia.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        nome_usuario = request.form.get('nome_usuario', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not nome_usuario or not email or not senha:
            flash('Preencha todos os campos.')
            return redirect(url_for('cadastro'))

        if senha != confirmar_senha:
            flash('As senhas não coincidem.')
            return redirect(url_for('cadastro'))

        senha_hash = generate_password_hash(senha)
        conexao = conectar_bd()
        try:
            conexao.execute('''
                INSERT INTO usuarios (nomeUsuario, nomeCadastroUsuario, emailUsuario, senhaUsuario)
                VALUES (?, ?, ?, ?)
            ''', (nome, nome_usuario, email, senha_hash))
            conexao.commit()
        except sqlite3.IntegrityError:
            flash('Esse nome de usuário ou e-mail já está cadastrado.')
            conexao.close()
            return redirect(url_for('cadastro'))
        conexao.close()

        flash('Cadastro feito com sucesso! Faça login para continuar.')
        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        senha = request.form.get('senha', '')
        proxima = request.form.get('proxima') or request.args.get('proxima')

        conexao = conectar_bd()
        usuario = conexao.execute('''
            SELECT * FROM usuarios WHERE emailUsuario = ? OR nomeCadastroUsuario = ?
        ''', (identificador, identificador)).fetchone()
        conexao.close()

        if usuario and check_password_hash(usuario['senhaUsuario'], senha):
            session['usuario_id'] = usuario['idUsuario']
            session['usuario_nome'] = usuario['nomeCadastroUsuario']
            return redirect(proxima or url_for('fas'))

        flash('E-mail/usuário ou senha incorretos.')
        return redirect(url_for('login', proxima=proxima))

    proxima = request.args.get('proxima', '')
    return render_template('login.html', proxima=proxima)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('fas'))


@app.route('/fas')
def fas():
    conexao = conectar_bd()
    posts = conexao.execute('''
        SELECT
            post.idPost,
            post.textoPost AS conteudo,
            post.imagemPost AS imagem,
            post.dataPost,
            usuarios.nomeCadastroUsuario,
            (SELECT COUNT(*) FROM curtidas WHERE curtidas.idPost = post.idPost) AS totalCurtidas,
            (SELECT COUNT(*) FROM comentarios WHERE comentarios.idPost = post.idPost) AS totalComentarios
        FROM post
        JOIN usuarios ON post.idUsuario = usuarios.idUsuario
        ORDER BY post.dataPost DESC
    ''').fetchall()

    curtidas_usuario = set()
    if 'usuario_id' in session:
        linhas = conexao.execute(
            'SELECT idPost FROM curtidas WHERE idUsuario = ?', (session['usuario_id'],)
        ).fetchall()
        curtidas_usuario = {linha['idPost'] for linha in linhas}

    comentarios_por_post = {}
    for post in posts:
        comentarios = conexao.execute('''
            SELECT comentarios.textComentarios, comentarios.dataComentarios, usuarios.nomeCadastroUsuario
            FROM comentarios
            JOIN usuarios ON comentarios.idUsuario = usuarios.idUsuario
            WHERE comentarios.idPost = ?
            ORDER BY comentarios.dataComentarios ASC
        ''', (post['idPost'],)).fetchall()
        comentarios_por_post[post['idPost']] = comentarios

    conexao.close()
    return render_template(
        'fas.html',
        posts=posts,
        curtidas_usuario=curtidas_usuario,
        comentarios_por_post=comentarios_por_post,
    )


@app.route('/cadastrar_post', methods=['POST'])
@login_necessario
def cadastrar_post():
    conteudo = request.form.get('conteudo')
    arquivo_imagem = request.files.get('imagem')
    caminho_imagem = None

    if arquivo_imagem and arquivo_imagem.filename != '':
        nome_imagem = secure_filename(arquivo_imagem.filename)
        caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)
        arquivo_imagem.save(caminho_completo)
        caminho_imagem = f"uploads/{nome_imagem}"

    conexao = conectar_bd()
    conexao.execute('''
        INSERT INTO post (idUsuario, textoPost, imagemPost)
        VALUES (?, ?, ?)
    ''', (session['usuario_id'], conteudo, caminho_imagem))
    conexao.commit()
    conexao.close()

    return redirect(url_for('fas'))


@app.route('/curtir_post/<int:id_post>', methods=['POST'])
@login_necessario
def curtir_post(id_post):
    usuario_id = session['usuario_id']
    conexao = conectar_bd()
    ja_curtiu = conexao.execute(
        'SELECT 1 FROM curtidas WHERE idPost = ? AND idUsuario = ?', (id_post, usuario_id)
    ).fetchone()

    if ja_curtiu:
        conexao.execute(
            'DELETE FROM curtidas WHERE idPost = ? AND idUsuario = ?', (id_post, usuario_id)
        )
    else:
        conexao.execute(
            'INSERT INTO curtidas (idPost, idUsuario) VALUES (?, ?)', (id_post, usuario_id)
        )

    conexao.commit()
    conexao.close()
    return redirect(url_for('fas'))


@app.route('/comentar_post/<int:id_post>', methods=['POST'])
@login_necessario
def comentar_post(id_post):
    texto = request.form.get('texto_comentario', '').strip()
    if texto:
        conexao = conectar_bd()
        conexao.execute('''
            INSERT INTO comentarios (idPost, idUsuario, textComentarios)
            VALUES (?, ?, ?)
        ''', (id_post, session['usuario_id'], texto))
        conexao.commit()
        conexao.close()
    return redirect(url_for('fas'))


if __name__ == '__main__':
    app.run(debug=True)
