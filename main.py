from flask import Flask, render_template, request, flash, redirect, url_for
import fdb

app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave_secreta_da_turma_b'

host = 'localhost'
database = r'C:\Users\Aluno\Downloads\BANCO_bia\BANCOBIA.FDB'
user = 'sysdba'
password = 'sysdba'

con = fdb.connect(host=host, database=database, user=user, password=password)

@app.route('/')
def index():
    cursor = con.cursor()

    cursor.execute("""SELECT l.id_livro, l.titulo, l.autor, l.data_publicacao 
    FROM LIVRO l
    order by l.data_publicacao""" )

    livros = cursor.fetchall()

    cursor.close()

    return render_template('livro.html', livros=livros)

@app.route('/novo')
def novo():
    return render_template("novo.html")

@app.route('/criar', methods = ['POST'])
def criar():
    titulo = request.form['titulo']
    autor = request.form['autor']
    data_publicacao = request.form['data_publicacao']

    cursor = con.cursor()

    try:
        cursor.execute("""SELECT 1 FROM livro WHERE titulo = ?""", (titulo,))
        if cursor.fetchone():
            flash("Erro: livro já existe no banco")
            return redirect(url_for('novo'))

        cursor.execute(""" 
                            INSERT INTO livro (titulo, autor, DATA_PUBLICACAO)
                            values(?,?,?) 
                        """, (titulo, autor, data_publicacao))

        con.commit() #salva no banco
        flash("Livro criado com sucesso")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        con.rollback()
        return redirect(url_for('index'))
    finally:
        cursor.close()

@app.route('/editar/<int:id>', methods = ['GET', 'POST'])
def editar(id):

    cursor = con.cursor()
    try:
        cursor.execute("""SELECT id_livro, titulo, autor, data_publicacao
                        FROM livro WHERE id_livro = ?""", (id,))
        livro = cursor.fetchone()

        if not livro:
            flash("Livro não encontrado")
            return redirect(url_for('index'))

        if request.method == 'POST':
            titulo = request.form['titulo']
            autor = request.form['autor']
            data_publicacao = request.form['data_publicacao']

            cursor.execute(""" UPDATE livro SET titulo = ?, autor = ?, data_publicacao = ? where id_livro = ?""", (titulo, autor, data_publicacao, id))
            con.commit()
            flash("Livro editado com sucesso")
            return redirect(url_for('index'))

        return render_template("editar.html", livro=livro)

    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        con.rollback()
        return redirect(url_for('index'))
    finally:
        cursor.close()



@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):

    cursor = con.cursor()

    try:
        cursor.execute(
            "DELETE FROM livro WHERE id_livro = ?",
            (id,)
        )

        con.commit()

        flash("Livro excluído com sucesso")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Ocorreu um erro -> {e}")
        con.rollback()
        return redirect(url_for('index'))

    finally:
        cursor.close()



if __name__ == '__main__':
    app.run(debug=True)