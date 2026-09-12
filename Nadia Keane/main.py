import sqlite3
from werkzeug.security import generate_password_hash

conexao = sqlite3.connect("bancoNK.db")
cursor = conexao.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios (
                idUsuario INTEGER PRIMARY KEY AUTOINCREMENT,
                nomeUsuario VARCHAR(200) NOT NULL,
                nomeCadastroUsuario VARCHAR(200) NOT NULL UNIQUE,
                emailUsuario VARCHAR(150) NOT NULL UNIQUE,
                senhaUsuario VARCHAR(250) NOT NULL,
                dataUsuario DATETIME DEFAULT CURRENT_TIMESTAMP
                )""")

cursor.execute("""CREATE TABLE IF NOT EXISTS post (
                idPost INTEGER PRIMARY KEY AUTOINCREMENT,
                idUsuario INTEGER NOT NULL,
                textoPost TEXT,
                imagemPost VARCHAR(200),
                dataPost DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (idUsuario) REFERENCES usuarios(idUsuario)
                )""")

cursor.execute("""CREATE TABLE IF NOT EXISTS comentarios (
                idComentarios INTEGER PRIMARY KEY AUTOINCREMENT,
                idPost INTEGER NOT NULL, 
                idUsuario INTEGER NOT NULL,
                textComentarios TEXT NOT NULL,
                dataComentarios DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (idPost) REFERENCES post(idPost),
                FOREIGN KEY (idUsuario) REFERENCES usuarios(idUsuario)
                )""")
cursor.execute("""CREATE TABLE IF NOT EXISTS curtidas (
                idPost INTEGER NOT NULL, 
                idUsuario INTEGER NOT NULL,
                PRIMARY KEY (idUsuario, idPost),

                FOREIGN KEY (idPost) REFERENCES post(idPost),
                FOREIGN KEY (idUsuario) REFERENCES usuarios(idUsuario)
                )""")

senha_hash = generate_password_hash('senha123')
cursor.execute("""INSERT INTO usuarios (nomeUsuario, nomeCadastroUsuario, emailUsuario, senhaUsuario)
                VALUES ('Axx', 'Axx_Nk', 'axxcnk@email.com', ?)
                """, (senha_hash,))

conexao.commit()
conexao.close()
