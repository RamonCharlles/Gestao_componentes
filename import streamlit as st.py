
import streamlit as st
import pandas as pd
import datetime
import os

# ─── Diretórios ──────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
os.makedirs("images/uploads", exist_ok=True)

CSV_PATH = "data/registros.csv"

# ─── Criação do CSV se necessário ────────────────────────────────────────────
if not os.path.exists(CSV_PATH):
    df = pd.DataFrame(columns=[
        "Responsável", "Matrícula", "PN", "Descrição", "TAG",
        "Horímetro", "Falha", "Escopo", "Imagem",
        "OS_Retirada", "Data_Retirada", "Status",
        "RS", "Nota/Passe", "Data_Envio", "Data_Entrega",
        "Cancelado", "Motivo_Cancelamento"
    ])
    df.to_csv(CSV_PATH, index=False)
else:
    df = pd.read_csv(CSV_PATH)

# ─── Página ─────────────────────────────────────────────────────────────────
st.set_page_config("Gestão de Componentes Reformáveis", layout="wide")
st.title("🛠 Gestão de Componentes Reformáveis")

menu = st.sidebar.radio("Perfil", ["Técnico de Campo", "Supervisor", "Administrador"])

def salvar_dados(df):
    df.to_csv(CSV_PATH, index=False)

# ==============================
# TÉCNICO DE CAMPO
# ==============================
if menu == "Técnico de Campo":
    st.subheader("📥 Cadastro de Componente Retirado")

    resumo = None
    with st.form("form_tecnico"):
        responsavel   = st.text_input("Responsável")
        matricula     = st.text_input("Matrícula")
        pn            = st.text_input("PN do Componente")
        descricao     = st.text_input("Descrição do Componente")
        tag           = st.text_input("TAG do Equipamento")
        horimetro     = st.number_input("Horímetro", 0)
        falha         = st.text_area("Falha apresentada")
        escopo        = st.text_area("Escopo do serviço")
        imagem        = st.file_uploader("Imagem (opcional)", type=["jpg", "png", "jpeg"])
        os_retirada   = st.text_input("OS de Retirada")
        data_retirada = st.date_input("Data da Retirada", datetime.date.today())
        submit        = st.form_submit_button("Salvar")

        if submit:
            img_path = ""
            if imagem:
                img_path = f"images/uploads/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{imagem.name}"
                with open(img_path, "wb") as f:
                    f.write(imagem.read())

            novo = {
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
                "Data_Entrega": "", "Cancelado": "Não", "Motivo_Cancelamento": ""
            }

            df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
            salvar_dados(df)
            st.success("✅ Componente cadastrado com sucesso!")

            id_registro = len(df)
            resumo = f"ID: {id_registro}\nDescrição: {descricao}\nPN: {pn}"

    if resumo:
        st.markdown("### 📋 Resumo do Cadastro:")
        st.code(resumo)
        st.button("📋 Copiar resumo")
        st.info("Copie manualmente com Ctrl+C para compartilhar.")

# ==============================
# SUPERVISOR
# ==============================
elif menu == "Supervisor":
    st.subheader("🔐 Acesso do Supervisor")
    user  = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if user in st.secrets.supervisores and st.secrets.supervisores[user] == senha:
        st.success("Acesso liberado.")

        pendentes = df[df["Status"] == "Aguardando Envio"]
        if not pendentes.empty:
            st.markdown("### ✏️ Selecionar processo pendente")
            idx = st.selectbox(
                "Selecionar para tratar",
                pendentes.index,
                format_func=lambda i: f"{df.at[i,'PN']} — {df.at[i,'TAG']} — {df.at[i,'Responsável']}"
            )

            item = df.loc[idx]
            st.markdown(f"**Descrição:** {item['Descrição']}  
**PN:** {item['PN']}  
**TAG:** {item['TAG']}  
**Falha:** {item['Falha']}")
            if pd.notna(item["Imagem"]) and os.path.exists(item["Imagem"]):
                st.image(item["Imagem"], width=400, caption=f'{item["PN"]} - {item["Descrição"]}')
                with open(item["Imagem"], "rb") as f:
                    st.download_button(
                        label="📥 Baixar Imagem",
                        data=f,
                        file_name=os.path.basename(item["Imagem"]),
                        mime="image/jpeg"
                    )

            with st.form("form_supervisor"):
                rs         = st.text_input("Nº da RS")
                nota       = st.text_input("Nota Fiscal / Passe")
                data_envio = st.date_input("Data de Envio", datetime.date.today())
                submit_envio = st.form_submit_button("Confirmar envio")

                if submit_envio:
                    df.at[idx, "RS"] = rs
                    df.at[idx, "Nota/Passe"] = nota
                    df.at[idx, "Data_Envio"] = str(data_envio)
                    df.at[idx, "Status"] = "Aguardando Retorno"
                    salvar_dados(df)
                    st.success("✅ Processo enviado. Status atualizado para 'Aguardando Retorno'.")

        else:
            st.info("Nenhum item pendente para envio.")

        st.markdown("### 📦 Atualizar para 'Componente Entregue'")
        retorno = df[df["Status"] == "Aguardando Retorno"]
        if not retorno.empty:
            idx2 = st.selectbox(
                "Selecionar item para dar baixa",
                retorno.index,
                format_func=lambda i: f"{df.at[i,'PN']} — {df.at[i,'TAG']}"
            )
            with st.form("form_entrega"):
                data_entrega = st.date_input("Data de Entrega", datetime.date.today())
                submit_entrega = st.form_submit_button("Confirmar Entrega")
                if submit_entrega:
                    df.at[idx2, "Status"] = "Componente Entregue"
                    df.at[idx2, "Data_Entrega"] = str(data_entrega)
                    salvar_dados(df)
                    st.success("✅ Item dado como entregue.")
        else:
            st.info("Nenhum item aguardando retorno.")
    else:
        st.warning("Usuário ou senha incorretos.")

# ==============================
# ADMINISTRADOR
# ==============================
elif menu == "Administrador":
    st.subheader("🔐 Acesso do Administrador")
    user  = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if user in st.secrets.admin and st.secrets.admin[user] == senha:
        st.success("Acesso completo concedido.")
        st.markdown("### 📋 Relatórios por Status")

        pend = df[df["Status"] == "Aguardando Envio"]
        envio = df[df["Status"] == "Aguardando Retorno"]
        entregue = df[df["Status"] == "Componente Entregue"]

        st.markdown("#### 📍 Pendentes de Envio")
        st.dataframe(pend)

        st.markdown("#### 🚚 Enviados e Aguardando Retorno")
        st.dataframe(envio)

        st.markdown("#### ✅ Componentes Entregues")
        st.dataframe(entregue)

        st.download_button("📥 Baixar todos os dados (CSV)", df.to_csv(index=False), "componentes.csv", "text/csv")
    else:
        st.warning("Usuário ou senha incorretos.")

