import streamlit as st
import pandas as pd
import datetime
import os

# Criação de diretórios se não existirem
os.makedirs("data", exist_ok=True)
os.makedirs("images/uploads", exist_ok=True)

# Caminho do CSV
CSV_PATH = "data/registros.csv"

# Inicializa o CSV se não existir
if not os.path.exists(CSV_PATH):
    df = pd.DataFrame(columns=[
        "Responsável", "Matrícula", "PN", "Descrição", "TAG",
        "Horímetro", "Falha", "Escopo", "Imagem",
        "OS_Retirada", "Data_Retirada", "Status",
        "RS", "Nota/Passe", "Data_Envio",
        "Cancelado", "Motivo_Cancelamento"
    ])
    df.to_csv(CSV_PATH, index=False)
else:
    df = pd.read_csv(CSV_PATH)

# Configuração da página
st.set_page_config("Gestão de Componentes Reformáveis", layout="wide")
st.title("🛠 Gestão de Componentes Reformáveis")

# Menu lateral
menu = st.sidebar.radio("Escolha o Perfil", ["Técnico de Campo", "Supervisor", "Administrador"])

# Função para salvar alterações
def salvar_dados(df):
    df.to_csv(CSV_PATH, index=False)

# =============================
# TECNICO DE CAMPO
# =============================
if menu == "Técnico de Campo":
    st.subheader("📥 Cadastro de Componente Retirado")

    with st.form("form_tecnico"):
        responsavel = st.text_input("Responsável")
        matricula = st.text_input("Matrícula")
        pn = st.text_input("PN do Componente")
        descricao = st.text_input("Descrição do Componente")
        tag = st.text_input("TAG do Equipamento")
        horimetro = st.number_input("Horímetro", 0)
        falha = st.text_area("Falha apresentada")
        escopo = st.text_area("Escopo do serviço")
        imagem = st.file_uploader("Imagem do componente (opcional)", type=["jpg", "png", "jpeg"])
        os_retirada = st.text_input("OS de Retirada")
        data_retirada = st.date_input("Data da Retirada", datetime.date.today())
        submit = st.form_submit_button("Salvar")

        if submit:
            img_path = ""
            if imagem:
                img_path = f"images/uploads/{imagem.name}"
                with open(img_path, "wb") as f:
                    f.write(imagem.read())

            novo = pd.DataFrame([{
                "Responsável": responsavel,
                "Matrícula": matricula,
                "PN": pn,
                "Descrição": descricao,
                "TAG": tag,
                "Horímetro": horimetro,
                "Falha": falha,
                "Escopo": escopo,
                "Imagem": img_path,
                "OS_Retirada": os_retirada,
                "Data_Retirada": str(data_retirada),
                "Status": "Aguardando Envio",
                "RS": "", "Nota/Passe": "", "Data_Envio": "",
                "Cancelado": "Não", "Motivo_Cancelamento": ""
            }])
            df = pd.concat([df, novo], ignore_index=True)
            salvar_dados(df)
            st.success("✅ Componente cadastrado com sucesso!")

# =============================
# SUPERVISOR
# =============================
elif menu == "Supervisor":
    st.subheader("🔐 Acesso do Supervisor")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if user in st.secrets.supervisores and st.secrets.supervisores[user] == senha:
        st.success("Acesso liberado.")
        pendentes = df[df["Status"] == "Aguardando Envio"]

        if not pendentes.empty:
            idx = st.selectbox("Selecionar componente para atualizar", pendentes.index)
            with st.form("form_supervisor"):
                status = st.selectbox("Status", ["Enviado para Reforma", "Cancelado"])
                rs = st.text_input("Nº da RS")
                nota = st.text_input("Nota Fiscal / Passe de saída")
                data_envio = st.date_input("Data de Envio", datetime.date.today())
                motivo = ""
                if status == "Cancelado":
                    motivo = st.text_area("Motivo do Cancelamento")
                submit_sup = st.form_submit_button("Salvar Atualização")

                if submit_sup:
                    df.at[idx, "Status"] = status
                    df.at[idx, "RS"] = rs
                    df.at[idx, "Nota/Passe"] = nota
                    df.at[idx, "Data_Envio"] = str(data_envio)
                    df.at[idx, "Cancelado"] = "Sim" if status == "Cancelado" else "Não"
                    df.at[idx, "Motivo_Cancelamento"] = motivo
                    salvar_dados(df)
                    st.success("✅ Atualização salva com sucesso.")
        else:
            st.info("Nenhum componente aguardando envio.")
    else:
        st.warning("Usuário ou senha incorretos.")

# =============================
# ADMINISTRADOR
# =============================
elif menu == "Administrador":
    st.subheader("🔐 Acesso do Administrador")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if user in st.secrets.admin and st.secrets.admin[user] == senha:
        st.success("Bem-vindo, administrador.")

        st.markdown("### 📋 Dados Cadastrados")
        st.dataframe(df)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Recarregar dados"):
                df = pd.read_csv(CSV_PATH)
                st.experimental_rerun()

        with col2:
            st.download_button("📥 Baixar CSV", df.to_csv(index=False), "registros.csv", "text/csv")

    else:
        st.warning("Usuário ou senha incorretos.")
        

