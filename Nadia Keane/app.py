import os
import sqlite3
import uuid
from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
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

def salvar_imagem_enviada(arquivo):
    if not arquivo or arquivo.filename == '':
        return None

    extensao = os.path.splitext(secure_filename(arquivo.filename))[1].lower()
    if not extensao:
        extensao = '.jpg'

    nome_unico = f"{uuid.uuid4().hex}{extensao}"
    caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
    arquivo.save(caminho_completo)
    return f"uploads/{nome_unico}" 

@app.context_processor
def injetar_usuario():
    return dict(usuario_logado=session.get('usuario_nome'), id_usuario_logado=session.get('usuario_id'))

@app.route('/atualizar_foto_perfil', methods=['POST'])
@login_necessario
def atualizar_foto_perfil():
    caminho_foto = salvar_imagem_enviada(request.files.get('foto'))

    if caminho_foto:
        conexao = conectar_bd()
        conexao.execute(
            'UPDATE usuarios SET fotoPerfilUsuario = ? WHERE idUsuario = ?',
            (caminho_foto, session['usuario_id'])
        )
        conexao.commit()
        conexao.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True, foto=url_for('static', filename=caminho_foto) if caminho_foto else None)
    return redirect(url_for('fas'))

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
            post.idUsuario,
            post.textoPost AS conteudo,
            post.imagemPost AS imagem,
            post.dataPost,
            usuarios.nomeCadastroUsuario,
            usuarios.fotoPerfilUsuario,
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
            SELECT 
                    comentarios.idComentarios,
                    comentarios.idUsuario,
                    comentarios.textComentarios, 
                    comentarios.dataComentarios, 
                    usuarios.nomeCadastroUsuario
            FROM comentarios
            JOIN usuarios ON comentarios.idUsuario = usuarios.idUsuario
            WHERE comentarios.idPost = ?
            ORDER BY comentarios.dataComentarios ASC
        ''', (post['idPost'],)).fetchall()
        comentarios_por_post[post['idPost']] = comentarios

    foto_usuario_logado = None
    if 'usuario_id' in session:
        linha_usuario = conexao.execute(
            'SELECT fotoPerfilUsuario FROM usuarios WHERE idUsuario = ?', (session['usuario_id'],)
        ).fetchone()
        if linha_usuario:
            foto_usuario_logado = linha_usuario['fotoPerfilUsuario']

    conexao.close()
    return render_template(
        'fas.html',
        posts=posts,
        curtidas_usuario=curtidas_usuario,
        comentarios_por_post=comentarios_por_post,
        foto_usuario_logado=foto_usuario_logado,
    )


@app.route('/fasTeorias')
def fasTeorias():
    conexao = conectar_bd()

    teorias = conexao.execute('''
        SELECT
            teorias.idTeoria,
            teorias.idUsuario,
            teorias.textoTeoria AS conteudo,
            teorias.imagemTeoria AS imagem,
            teorias.dataTeoria,
            usuarios.nomeCadastroUsuario,
            usuarios.fotoPerfilUsuario,
            (
                SELECT COUNT(*)
                FROM curtidas_teorias
                WHERE curtidas_teorias.idTeoria = teorias.idTeoria
            ) AS totalCurtidas,
            (
                SELECT COUNT(*)
                FROM comentarios_teorias
                WHERE comentarios_teorias.idTeoria = teorias.idTeoria
            ) AS totalComentarios
        FROM teorias
        JOIN usuarios
            ON teorias.idUsuario = usuarios.idUsuario
        ORDER BY teorias.dataTeoria DESC
    ''').fetchall()

    curtidas_usuario = set()

    if 'usuario_id' in session:
        linhas = conexao.execute('''
            SELECT idTeoria
            FROM curtidas_teorias
            WHERE idUsuario = ?
        ''', (session['usuario_id'],)).fetchall()

        curtidas_usuario = {
            linha['idTeoria'] for linha in linhas
        }

    comentarios_por_teoria = {}

    for teoria in teorias:
        comentarios = conexao.execute('''
            SELECT
                comentarios_teorias.idComentarioTeoria AS idComentarios,
                comentarios_teorias.idUsuario,
                comentarios_teorias.textoComentario AS textComentarios,
                comentarios_teorias.dataComentario AS dataComentarios,
                usuarios.nomeCadastroUsuario
            FROM comentarios_teorias
            JOIN usuarios
                ON comentarios_teorias.idUsuario = usuarios.idUsuario
            WHERE comentarios_teorias.idTeoria = ?
            ORDER BY comentarios_teorias.dataComentario ASC
        ''', (teoria['idTeoria'],)).fetchall()

        comentarios_por_teoria[teoria['idTeoria']] = comentarios

    foto_usuario_logado = None

    if 'usuario_id' in session:
        linha_usuario = conexao.execute('''
            SELECT fotoPerfilUsuario
            FROM usuarios
            WHERE idUsuario = ?
        ''', (session['usuario_id'],)).fetchone()

        if linha_usuario:
            foto_usuario_logado = linha_usuario['fotoPerfilUsuario']

    conexao.close()

    return render_template(
        'fasTeorias.html',
        teorias=teorias,
        curtidas_usuario=curtidas_usuario,
        comentarios_por_teoria=comentarios_por_teoria,
        foto_usuario_logado=foto_usuario_logado
    )

@app.route('/fasPodCast')
def fasPodCast():
    return render_template('fasPodCast.html')


@app.route('/cadastrar_post', methods=['POST'])
@login_necessario
def cadastrar_post():
    conteudo = request.form.get('conteudo')
    # Agora usa nome único (UUID), igual às teorias e à foto de perfil
    caminho_imagem = salvar_imagem_enviada(request.files.get('imagem'))

    conexao = conectar_bd()
    conexao.execute('''
        INSERT INTO post (idUsuario, textoPost, imagemPost)
        VALUES (?, ?, ?)
    ''', (session['usuario_id'], conteudo, caminho_imagem))
    conexao.commit()
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True)
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
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True)
    return redirect(url_for('fas'))


@app.route('/comentar_post/<int:id_post>', methods=['POST'])
@login_necessario
def comentar_post(id_post):
    texto = request.form.get('texto_comentario', '').strip()
    novo_id = None
    total = 0
    if texto:
        conexao = conectar_bd()
        cursor = conexao.execute('''
            INSERT INTO comentarios (idPost, idUsuario, textComentarios)
            VALUES (?, ?, ?)
        ''', (id_post, session['usuario_id'], texto))
        conexao.commit()
        novo_id = cursor.lastrowid
        total = conexao.execute(
            'SELECT COUNT(*) AS total FROM comentarios WHERE idPost = ?', (id_post,)
        ).fetchone()['total']
        conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(
            idComentarios=novo_id,
            nomeCadastroUsuario=session.get('usuario_nome'),
            textComentarios=texto,
            total=total,
        )
    return redirect(url_for('fas'))

@app.route('/excluir_post/<int:id_post>', methods=['POST'])
@login_necessario
def excluir_post(id_post):
    conexao = conectar_bd()
    post = conexao.execute(
        'SELECT idUsuario, imagemPost FROM post WHERE idPost = ?', (id_post,)
    ).fetchone()

    if post and post['idUsuario'] == session['usuario_id']:
        conexao.execute('DELETE FROM post WHERE idPost = ?', (id_post,))
        conexao.commit()

        if post['imagemPost']:
            caminho_imagem = os.path.join(BASE_DIR, 'static', post['imagemPost'])
            if os.path.exists(caminho_imagem):
                try:
                    os.remove(caminho_imagem)
                except OSError:
                    pass
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True)
    return redirect(url_for('fas'))

@app.route('/excluir_comentario/<int:id_comentarios>', methods=['POST'])
@login_necessario
def excluir_comentario(id_comentarios):
    conexao = conectar_bd()
    comentario = conexao.execute(
        'SELECT idUsuario FROM comentarios WHERE idComentarios = ?', (id_comentarios,)
    ).fetchone()

    if comentario and comentario['idUsuario'] == session['usuario_id']:
        conexao.execute('DELETE FROM comentarios WHERE idComentarios = ?', (id_comentarios,))
        conexao.commit()
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True)
    return redirect(url_for('fas'))

@app.route('/cadastrar_teoria', methods=['POST'])
@login_necessario
def cadastrar_teoria():
    conteudo = request.form.get('conteudo', '').strip()
    arquivo_imagem = request.files.get('imagem')
    caminho_imagem = salvar_imagem_enviada(arquivo_imagem)
    if not conteudo and not caminho_imagem:
        flash('Escreva uma teoria ou escolha uma imagem.')
        return redirect(url_for('fasTeorias'))
    conexao = conectar_bd()
    conexao.execute('''
        INSERT INTO teorias (idUsuario, textoTeoria, imagemTeoria)
        VALUES (?, ?, ?)
    ''', (session['usuario_id'], conteudo, caminho_imagem))
    conexao.commit()
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True)
    return redirect(url_for('fasTeorias'))

@app.route('/curtir_teoria/<int:id_teoria>', methods=['POST'])
@login_necessario
def curtir_teoria(id_teoria):
    usuario_id = session['usuario_id']
    conexao = conectar_bd()
    teoria = conexao.execute(
        'SELECT idTeoria FROM teorias WHERE idTeoria = ?',
        (id_teoria,)
    ).fetchone()
    if not teoria:
        conexao.close()
        return jsonify(sucesso=False, erro='Teoria não encontrada.'), 404
    ja_curtiu = conexao.execute('''
        SELECT 1
        FROM curtidas_teorias
        WHERE idTeoria = ? AND idUsuario = ?
    ''', (id_teoria, usuario_id)).fetchone()
    if ja_curtiu:
        conexao.execute('''
            DELETE FROM curtidas_teorias
            WHERE idTeoria = ? AND idUsuario = ?
        ''', (id_teoria, usuario_id))
        curtiu = False
    else:
        conexao.execute('''
            INSERT INTO curtidas_teorias (idTeoria, idUsuario)
            VALUES (?, ?)
        ''', (id_teoria, usuario_id))
        curtiu = True
    total = conexao.execute('''
        SELECT COUNT(*) AS total
        FROM curtidas_teorias
        WHERE idTeoria = ?
    ''', (id_teoria,)).fetchone()['total']
    conexao.commit()
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True, curtiu=curtiu, total=total)
    return redirect(url_for('fasTeorias'))

@app.route('/comentar_teoria/<int:id_teoria>', methods=['POST'])
@login_necessario
def comentar_teoria(id_teoria):
    texto = request.form.get('texto_comentario', '').strip()
    if not texto:
        return redirect(url_for('fasTeorias'))
    conexao = conectar_bd()
    teoria = conexao.execute(
        'SELECT idTeoria FROM teorias WHERE idTeoria = ?',
        (id_teoria,)
    ).fetchone()
    if not teoria:
        conexao.close()
        return jsonify(sucesso=False, erro='Teoria não encontrada.'), 404
    cursor = conexao.execute('''
        INSERT INTO comentarios_teorias (idTeoria, idUsuario, textoComentario)
        VALUES (?, ?, ?)
    ''', (id_teoria, session['usuario_id'], texto))
    novo_id = cursor.lastrowid
    total = conexao.execute('''
        SELECT COUNT(*) AS total
        FROM comentarios_teorias
        WHERE idTeoria = ?
    ''', (id_teoria,)).fetchone()['total']
    conexao.commit()
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(
            idComentarios=novo_id,
            nomeCadastroUsuario=session.get('usuario_nome'),
            textComentarios=texto,
            total=total
        )

    return redirect(url_for('fasTeorias'))

@app.route('/excluir_teoria/<int:id_teoria>', methods=['POST'])
@login_necessario
def excluir_teoria(id_teoria):
    conexao = conectar_bd()
    teoria = conexao.execute('''
        SELECT idUsuario, imagemTeoria
        FROM teorias
        WHERE idTeoria = ?
    ''', (id_teoria,)).fetchone()
    if teoria and teoria['idUsuario'] == session['usuario_id']:
        conexao.execute(
            'DELETE FROM curtidas_teorias WHERE idTeoria = ?',
            (id_teoria,)
        )
        conexao.execute(
            'DELETE FROM comentarios_teorias WHERE idTeoria = ?',
            (id_teoria,)
        )
        conexao.execute(
            'DELETE FROM teorias WHERE idTeoria = ?',
            (id_teoria,)
        )
        conexao.commit()
        if teoria['imagemTeoria']:
            caminho = os.path.join(
                BASE_DIR, 'static', teoria['imagemTeoria']
            )
            if os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except OSError:
                    pass
    conexao.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(sucesso=True)
    return redirect(url_for('fasTeorias'))


@app.route('/excluir_comentario_teoria/<int:id_comentarios>', methods=['POST'])
@login_necessario
def excluir_comentario_teoria(id_comentarios):
    conexao = conectar_bd()
    try:
        comentario = conexao.execute('''
            SELECT idUsuario, idTeoria
            FROM comentarios_teorias
            WHERE idComentarioTeoria = ?
        ''', (id_comentarios,)).fetchone()
        if not comentario:
            return jsonify(
                sucesso=False,
                erro='Comentário não encontrado.'
            ), 404
        if comentario['idUsuario'] != session['usuario_id']:
            return jsonify(
                sucesso=False,
                erro='Você não pode excluir esse comentário.'
            ), 403
        id_teoria = comentario['idTeoria']
        conexao.execute('''
            DELETE FROM comentarios_teorias
            WHERE idComentarioTeoria = ?
        ''', (id_comentarios,))
        conexao.commit()
        total = conexao.execute('''
            SELECT COUNT(*) AS total
            FROM comentarios_teorias
            WHERE idTeoria = ?
        ''', (id_teoria,)).fetchone()['total']
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(
                sucesso=True,
                idComentarios=id_comentarios,
                total=total
            )
        return redirect(url_for('fasTeorias'))
    except sqlite3.Error:
        conexao.rollback()
        app.logger.exception('Erro ao excluir comentário da teoria.')
        return jsonify(
            sucesso=False,
            erro='Erro ao excluir comentário.'
        ), 500
    finally:
        conexao.close()

if __name__ == '__main__':
    app.run(debug=True)
