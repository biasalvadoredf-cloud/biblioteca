from flask import Flask, render_template, request, flash, redirect, url_for, session
import fdb
from flask_bcrypt import Bcrypt
from fpdf import FPDF
from flask import send_file

# =========================================================
# CONFIGURAÇÃO DO FLASK
# =======================================================
app = Flask(__name__)

bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'chave_secreta_da_turma_b'


# =========================================================
# CONEXÃO COM O BANCO
# =========================================================

host = 'localhost'
database = r'C:\Users\Aluno\Downloads\BANCO_bia\BANCOBIA.FDB'
user = 'sysdba'
password = 'sysdba'
con = fdb.connect(
    host=host,
    database=database,
    user=user,
    password=password
)

# =========================================================
# FUNÇÃO PARA VERIFICAR SENHA FORTE
# =========================================================

def senha_forte(senha):

    if len(senha) < 8:
        return False

    tem_maiuscula = False
    tem_minuscula = False
    tem_numero = False
    tem_especial = False

    for caractere in senha:

        if caractere >= 'A' and caractere <= 'Z':
            tem_maiuscula = True

        elif caractere >= 'a' and caractere <= 'z':
            tem_minuscula = True

        elif caractere >= '0' and caractere <= '9':
            tem_numero = True

        else:
            tem_especial = True

    if (tem_maiuscula and tem_minuscula and tem_numero and tem_especial):

        return True

    return False



# =========================================================
# HOME - ANTES DO LOGIN
# =========================================================

@app.route('/')
def home():
    return render_template('home.html')


# =========================================================
# PAINEL - DEPOIS DO LOGIN
# =========================================================

@app.route('/index')
def index():

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    return render_template('index.html')


# =========================================================
# LIVROS
# =========================================================

@app.route('/livro')
def livro():

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    cursor = con.cursor()

    try:

        cursor.execute("""
            SELECT
                l.id_livro,
                l.titulo,
                l.autor,
                l.data_publicacao
            FROM LIVRO l
            ORDER BY l.data_publicacao
        """)

        livros = cursor.fetchall()

        return render_template(
            'livro.html',
            livros=livros
        )

    except Exception as e:

        flash(f'Ocorreu um erro -> {e}')

        return redirect(url_for('index'))

    finally:

        cursor.close()


# =========================================================
# NOVO LIVRO
# =========================================================

@app.route('/novo')
def novo():

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    return render_template('novo.html')


# =========================================================
# CRIAR LIVRO
# =========================================================

@app.route('/criar', methods=['POST'])
def criar():

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    titulo = request.form['titulo']
    autor = request.form['autor']
    data_publicacao = request.form['data_publicacao']

    cursor = con.cursor()

    try:

        # Verifica se o livro já existe
        cursor.execute(
            """
            SELECT 1
            FROM livro
            WHERE titulo = ?
            """,
            (titulo,)
        )

        if cursor.fetchone():

            flash("Erro: livro já existe no banco")

            return redirect(url_for('novo'))

        # Insere o livro
        cursor.execute(
            """
            INSERT INTO livro
            (
                titulo,
                autor,
                DATA_PUBLICACAO
            )
            VALUES (?, ?, ?)
            RETURNING id_livro
            """,
            (
                titulo,
                autor,
                data_publicacao
            )
        )

        id_livro = cursor.fetchone()[0]

        con.commit()

        # Salva a imagem
        arquivo = request.files.get('imagem')

        if arquivo and arquivo.filename:

            arquivo.save(
                f'uploads/capa{id_livro}.jpg'
            )

        flash("Livro criado com sucesso")

        return redirect(url_for('livro'))

    except Exception as e:

        flash(f"Ocorreu um erro -> {e}")

        con.rollback()

        return redirect(url_for('novo'))

    finally:

        cursor.close()


# =========================================================
# EDITAR LIVRO
# =========================================================

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    cursor = con.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id_livro,
                titulo,
                autor,
                data_publicacao
            FROM livro
            WHERE id_livro = ?
            """,
            (id,)
        )

        livro = cursor.fetchone()

        if not livro:

            flash("Livro não encontrado")

            return redirect(url_for('livro'))

        if request.method == 'POST':

            titulo = request.form['titulo']

            autor = request.form['autor']

            data_publicacao = request.form['data_publicacao']

            cursor.execute(
                """
                UPDATE livro

                SET
                    titulo = ?,
                    autor = ?,
                    data_publicacao = ?

                WHERE id_livro = ?
                """,
                (
                    titulo,
                    autor,
                    data_publicacao,
                    id
                )
            )

            con.commit()

            flash("Livro editado com sucesso")

            return redirect(url_for('livro'))

        return render_template(
            'editar.html',
            livro=livro
        )

    except Exception as e:

        flash(f"Ocorreu um erro -> {e}")

        con.rollback()

        return redirect(url_for('livro'))

    finally:

        cursor.close()


# =========================================================
# EXCLUIR LIVRO
# =========================================================

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    cursor = con.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM livro
            WHERE id_livro = ?
            """,
            (id,)
        )

        con.commit()

        flash("Livro excluído com sucesso")

        return redirect(url_for('livro'))

    except Exception as e:

        flash(f"Ocorreu um erro -> {e}")

        con.rollback()

        return redirect(url_for('livro'))

    finally:

        cursor.close()


# =========================================================
# USUÁRIOS
# =========================================================

@app.route('/usuario')
def usuario():

    if 'id_usuario' not in session:
        flash('Precisa estar logado')
        return redirect(url_for('login'))

    cursor = con.cursor()

    try:

        cursor.execute(
            """
            SELECT
                u.ID_USUARIO,
                u.NOME,
                u.EMAIL,
                u.SENHA

            FROM USUARIO u

            ORDER BY u.NOME
            """
        )

        usuarios = cursor.fetchall()

        return render_template(
            'usuario.html',
            usuarios=usuarios
        )

    except Exception as e:

        flash(f'Ocorreu um erro -> {e}')

        return redirect(url_for('index'))

    finally:

        cursor.close()


# =========================================================
# NOVO USUÁRIO
# =========================================================

@app.route('/novo_usuario', methods=['GET', 'POST'])
def novo_usuario():

    # Abre a página de cadastro
    if request.method == 'GET':

        return render_template(
            'novo_usuario.html'
        )

    nome = request.form['nome']

    email = request.form['email']

    senha = request.form['senha']


    # Verifica senha forte
    if not senha_forte(senha):

        flash(
            "A senha deve ter pelo menos 8 caracteres, "
            "uma letra maiúscula, uma letra minúscula, "
            "um número e um caractere especial."
        )

        return redirect(
            url_for('novo_usuario')
        )


    cursor = con.cursor()

    try:

        # Verifica se o usuário já existe
        cursor.execute(
            """
            SELECT 1
            FROM usuario
            WHERE nome = ?
            """,
            (nome,)
        )

        if cursor.fetchone():

            flash(
                "Erro: usuário já existe no banco"
            )

            return redirect(
                url_for('novo_usuario')
            )


        # Criptografa a senha
        senha_hash = bcrypt.generate_password_hash(
            senha
        ).decode('utf-8')


        # Cadastra usuário
        cursor.execute(
            """
            INSERT INTO usuario
            (
                nome,
                email,
                senha
            )
            VALUES (?, ?, ?)
            """,
            (
                nome,
                email,
                senha_hash
            )
        )

        con.commit()

        flash(
            "Usuário criado com sucesso"
        )

        # Depois de cadastrar, vai para login
        return redirect(
            url_for('login')
        )

    except Exception as e:

        flash(
            f"Ocorreu um erro -> {e}"
        )

        con.rollback()

        return redirect(
            url_for('novo_usuario')
        )

    finally:

        cursor.close()


# =========================================================
# EDITAR USUÁRIO
# =========================================================

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):

    if 'id_usuario' not in session:

        flash('Precisa estar logado')

        return redirect(
            url_for('login')
        )

    cursor = con.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id_usuario,
                nome,
                email,
                senha

            FROM usuario

            WHERE id_usuario = ?
            """,
            (id,)
        )

        usuario = cursor.fetchone()


        if not usuario:

            flash(
                "Usuário não encontrado"
            )

            return redirect(
                url_for('usuario')
            )


        # EDIÇÃO
        if request.method == 'POST':

            nome = request.form['nome']

            email = request.form['email']

            senha = request.form['senha']


            # Verifica senha
            if not senha_forte(senha):

                flash(
                    "A senha deve ter pelo menos 8 caracteres, "
                    "uma letra maiúscula, uma letra minúscula, "
                    "um número e um caractere especial."
                )

                return redirect(
                    url_for(
                        'editar_usuario',
                        id=id
                    )
                )


            # Criptografa senha
            senha_hash = bcrypt.generate_password_hash(
                senha
            ).decode('utf-8')


            cursor.execute(
                """
                UPDATE usuario

                SET
                    nome = ?,
                    email = ?,
                    senha = ?

                WHERE id_usuario = ?
                """,
                (
                    nome,
                    email,
                    senha_hash,
                    id
                )
            )

            con.commit()

            flash(
                "Usuário editado com sucesso"
            )

            return redirect(
                url_for('usuario')
            )


        # ABRIR PÁGINA DE EDIÇÃO
        return render_template(
            'editar_usuario.html',
            usuario=usuario
        )


    except Exception as e:

        flash(
            f"Ocorreu um erro -> {e}"
        )

        con.rollback()

        return redirect(
            url_for('usuario')
        )

    finally:

        cursor.close()


# =========================================================
# EXCLUIR USUÁRIO
# =========================================================

@app.route('/delete_usuario/<int:id>', methods=['POST'])
def delete_usuario(id):

    if 'id_usuario' not in session:

        flash(
            'Precisa estar logado'
        )

        return redirect(
            url_for('login')
        )

    cursor = con.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM usuario
            WHERE id_usuario = ?
            """,
            (id,)
        )

        con.commit()

        flash(
            "Usuário excluído com sucesso"
        )

        return redirect(
            url_for('usuario')
        )

    except Exception as e:

        flash(
            f"Ocorreu um erro -> {e}"
        )

        con.rollback()

        return redirect(
            url_for('usuario')
        )

    finally:

        cursor.close()


# =========================================================
# LOGIN
# =========================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        senha = request.form['senha']

        cursor = con.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id_usuario,
                    nome,
                    email,
                    senha,
                    tentativas,
                    ativo
                FROM USUARIO
                WHERE email = ?
                """,
                (email,)
            )

            usuario = cursor.fetchone()

            if not usuario:
                flash('Usuário não encontrado')
                return redirect(url_for('login'))

            id_usuario, nome, email, senha_hash, tentativas, ativo = usuario

            # Verifica se o usuário está ativo
            if ativo == 0:
                flash('Usuário inativo ou bloqueado.')
                return redirect(url_for('login'))

            # Verifica a senha
            if bcrypt.check_password_hash(senha_hash, senha):

                session['id_usuario'] = id_usuario
                session['usuario_nome'] = nome

                # Zera as tentativas
                cursor.execute(
                    'UPDATE usuario SET tentativas = ? WHERE id_usuario = ?',
                    (0, id_usuario)
                )

                con.commit()

                flash("Login realizado com sucesso")
                return redirect(url_for('index'))

            else:

                # Senha incorreta
                tentativas += 1

                cursor.execute(
                    'UPDATE usuario SET tentativas = ? WHERE id_usuario = ?',
                    (tentativas, id_usuario)
                )

                con.commit()

                if tentativas == 3:

                    cursor.execute(
                        'UPDATE usuario SET tentativas = ?, ativo = ? WHERE id_usuario = ?',
                        (tentativas, 0, id_usuario)
                    )

                    con.commit()

                    flash('Usuário bloqueado após 3 tentativas.')
                    return redirect(url_for('login'))

                flash(f"Email ou senha incorretos. Tentativa {tentativas} de 3.")
                return redirect(url_for('login'))

        except Exception as e:

            flash(f"Ocorreu um erro -> {e}")
            con.rollback()

            return redirect(url_for('login'))

        finally:

            cursor.close()

    return render_template('login.html')

# =========================================================
# LOGOUT
# =========================================================

@app.route('/logout')
def logout():

    session.pop('id_usuario',None)
    flash("Logout realizado com sucesso")
    return redirect(url_for('home'))

# =========================================================
# GERAR PDF
# =========================================================

@app.route('/livros/relatorio', methods=['GET'])
def relatorio():

    cursor = con.cursor()

    cursor.execute("""
        SELECT id_livro, titulo, autor, data_publicacao
        FROM livro
    """)

    livros = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatório de Livros", ln=True, align='C')

    pdf.ln(5)  # Espaço entre o título e a linha
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
    pdf.ln(5)  # Espaço após a linha

    pdf.set_font("Arial", size=12)

    for livro in livros:
        pdf.cell(
            200,
            10,
            f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}",
            ln=True
        )

    contador_livros = len(livros)

    pdf.ln(10)  # Espaço antes do contador

    pdf.set_font("Arial", style='B', size=12)

    pdf.cell(
        200,
        10,
        f"Total de livros cadastrados: {contador_livros}",
        ln=True,
        align='C'
    )

    pdf_path = "relatorio_livros.pdf"

    pdf.output(pdf_path)

    return send_file(
        pdf_path,
        as_attachment=True,
        mimetype='application/pdf'
    )



# =========================================================
# INICIAR SISTEMA
# =========================================================

if __name__ == '__main__':

    app.run(debug=True)