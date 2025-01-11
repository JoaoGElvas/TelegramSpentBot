import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Ler o token do arquivo token.txt
with open("token.txt", "r") as file:
    TOKEN = file.read().strip()

# Conectar ao banco de dados SQLite (cria o arquivo se não existir)
conn = sqlite3.connect("gastos.db")
cursor = conn.cursor()

# Criar a tabela de gastos, se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    valor REAL NOT NULL,
    descricao TEXT NOT NULL
)
""")
conn.commit()

# Criar a tabela de limites, se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS limites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    limite REAL NOT NULL
)
""")
conn.commit()

# Função para responder ao comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! Eu sou o MoneyBot, seu assistente de controle de gastos 🚀\n\n"
        "💰 Use /gasto [valor] [descricao] para registrar um gasto.\n"
        "📊 Use /resumo para ver o resumo dos seus gastos.\n"
        "🔻 Use /limite [valor] para definir seu limite de gastos.\n\n"
        "Exemplo: /gasto 50 almoço \n\n"
        "Criação de João Gabriel Elvas"
    )

# Função para definir o limite de gastos
async def definir_limite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        novo_limite = float(context.args[0])
        user_id = update.message.from_user.id

        # Salvar o limite no banco de dados
        cursor.execute("DELETE FROM limites WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT INTO limites (user_id, limite) VALUES (?, ?)", (user_id, novo_limite))
        conn.commit()

        await update.message.reply_text(f"✅ Seu novo limite de gastos foi definido para R${novo_limite:.2f}.")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Formato inválido. Use: /limite [valor]")

# Função para registrar um gasto
async def registrar_gasto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        valor = float(context.args[0])
        descricao = context.args[1]
        user_id = update.message.from_user.id

        # Salvar o gasto no banco de dados
        cursor.execute("INSERT INTO gastos (user_id, valor, descricao) VALUES (?, ?, ?)", (user_id, valor, descricao))
        conn.commit()

        await update.message.reply_text(f"✅ Gasto registrado: R${valor:.2f} ({descricao})")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Formato inválido. Use: /gasto [valor] [descricao]")

# Função para mostrar o resumo dos gastos
async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    # Obter os gastos do usuário atual
    cursor.execute("SELECT valor, descricao FROM gastos WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("💰 Você ainda não registrou nenhum gasto.")
        return

    # Calcular o total de gastos
    total = sum(valor for valor, descricao in rows)
    resumo_gastos = "\n".join([f"- R${valor:.2f}: {descricao}" for valor, descricao in rows])

    # Exibir o resumo
    mensagem = f"📊 Resumo dos seus gastos:\n\n{resumo_gastos}\n\n💵 Total: R${total:.2f}"

    # Obter o limite de gastos do usuário atual
    cursor.execute("SELECT limite FROM limites WHERE user_id = ?", (user_id,))
    limite_row = cursor.fetchone()

    if limite_row:
        limite_gastos = limite_row[0]
        limite_restante = limite_gastos - total
        porcentagem_limite = (total / limite_gastos) * 100 if limite_gastos > 0 else 0
        mensagem += f"\n\n🔻 Limite Restante: {100 - porcentagem_limite:.0f}%"

        # Notificar quando o limite estiver abaixo de 15%
        if limite_gastos - total < limite_gastos * 0.15:
            await update.message.reply_text(f"⚠️ Atenção: Seu limite de gastos está abaixo de 15%! Você já gastou R${total:.2f} de R${limite_gastos:.2f}.")

    await update.message.reply_text(mensagem)

# Configurar o bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", registrar_gasto))
    app.add_handler(CommandHandler("resumo", resumo))
    app.add_handler(CommandHandler("limite", definir_limite))

    print("Bot está rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()