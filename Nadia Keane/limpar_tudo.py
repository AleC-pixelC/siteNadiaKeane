import sqlite3

conexao = sqlite3.connect("bancoNK.db")
cursor = conexao.cursor()

cursor.execute("DELETE FROM curtidas")
cursor.execute("DELETE FROM comentarios")
cursor.execute("DELETE FROM post")
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('post', 'comentarios')")

conexao.commit()
conexao.close()
print("Todos os posts, comentários e curtidas foram apagados.")