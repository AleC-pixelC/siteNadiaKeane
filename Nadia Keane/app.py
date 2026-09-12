import os 
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chave_secreta_nadia_keane"

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def conectar_bd():
    conexao = sqlite3.connect("bancoNK.db")
    conexao.row_factory = sqlite3.Row
    return conexao

@app.route('/')
def inicio():
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

@app.route('/fas')
def fas():
    conexao = conectar_bd()
    posts = conexao.execute('''
        SELECT 
            post.idPost,
            post.textoPost AS conteudo,
            post.imagemPost AS imagem,
            post.dataPost,
            usuarios.nomeCadastroUsuario
        FROM post
        JOIN usuarios ON post.idUsuario = usuarios.idUsuario
        ORDER BY post.dataPost DESC
    ''').fetchall()
    conexao.close()
    return render_template('fas.html', posts=posts)

@app.route('/cadastrar_post', methods=['POST'])
def cadastrar_post():
    conteudo = request.form.get('conteudo')
    arquivo_imagem = request.files.get('imagem')
    caminho_imagem = None

    if arquivo_imagem and arquivo_imagem.filename != '':
        nome_imagem = secure_filename(arquivo_imagem.filename)
        caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)
        arquivo_imagem.save(caminho_completo)
        caminho_imagem = f"uploads/{nome_imagem}"

    id_usuario_teste = 1

    conexao = conectar_bd()
    conexao.execute('''
        INSERT INTO post (idUsuario, textoPost, imagemPost)
        VALUES (?, ?, ?)
    ''', (id_usuario_teste, conteudo, caminho_imagem))
    conexao.commit()
    conexao.close()

    return redirect(url_for('fas'))

if __name__ == '__main__':
    app.run(debug=True)