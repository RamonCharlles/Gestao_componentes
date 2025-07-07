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

# ─── Configuração de página ──────────────────────────────────────────────────
st.set_page_config("Gestão de Componentes Reformáveis", layout="wide")
st.title("🛠 Gestão de Componentes Reformáveis")

menu = st.sidebar.radio("Escolha o Perfil", ["Técnico de Campo", "Supervisor", "Administrador"])

def salvar_dados(df):
    df.to_csv(CSV_PATH, index=False)

# ==============================
# TÉCNICO DE CAMPO
# ==============================
if menu == "Técnico de Campo":
    st.subheader("📥 Cadastro de Componente Retirado")

    with st.form("form_tecnico"):
        responsavel   = st.text_input("Responsável")
        matricula     = st.text_input("Matrícula")
        pn            = st.text_input("PN do Componente")
        descricao     = st.text_input("Descrição do Componente")
        tag           = st.text_input("TAG do Equipamento")
        horimetro     = st.number_input("Horímetro", 0)
        falha         = st.text_area("Falha apresentada")
        escopo        = st.text_area("Escopo do serviço")
        imagem        = st.file_uploader("Imagem do componente (opcional)", type=["jpg", "png", "jpeg"])
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

            st.markdown("### 📋 Resumo do Cadastro:")
            st.code(resumo)

            if st.button("📋 Copiar resumo"):
                st.toast("Copie manualmente o texto acima (área de transferência automática depende do navegador).")

# ==============================
# SUPERVISOR
# ==============================
elif menu == "Supervisor":
    st.subheader("🔐 Acesso do Supervisor")
    user  = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if user in st.secrets.supervisores and st.secrets.supervisores[user] == senha:
        st.success("Acesso liberado.")

        st.markdown("### 🔍 Filtros de Pesquisa")
        status_opcao = st.multiselect("Status", df["Status"].unique(), default=list(df["Status"].unique()))
        tag_opcao    = st.multiselect("TAG do Equipamento", df["TAG"].unique(), default=list(df["TAG"].unique()))
        data_min     = st.date_input("Data inicial", datetime.date(2024, 1, 1))
        data_max     = st.date_input("Data final", datetime.date.today())

        df_filtrado = df[
            df["Status"].isin(status_opcao) &
            df["TAG"].isin(tag_opcao) &
            (pd.to_datetime(df["Data_Retirada"]) >= pd.to_datetime(data_min)) &
            (pd.to_datetime(df["Data_Retirada"]) <= pd.to_datetime(data_max))
        ]
        st.markdown(f"### 📋 Resultados ({len(df_filtrado)} registros)")
        st.dataframe(df_filtrado)

        st.markdown("### 🖼️ Visualizar Imagens")
        for i, row in df_filtrado.iterrows():
            if pd.notna(row["Imagem"]) and os.path.exists(row["Imagem"]):
                st.image(row["Imagem"], width=400, caption=f'{row["PN"]} - {row["Descrição"]}')
                with open(row["Imagem"], "rb") as f:
                    st.download_button(
                        label="📥 Baixar Imagem",
                        data=f,
                        file_name=os.path.basename(row["Imagem"]),
                        mime="image/jpeg"
                    )
                st.markdown("---")

        pendentes = df[df["Status"] == "Aguardando Envio"]
        if not pendentes.empty:
            st.markdown("### ✏️ Atualizar componente pendente")
            idx = st.selectbox(
                "Selecionar para atualizar",
                pendentes.index,
                format_func=lambda i: f"{df.at[i,'PN']} — {df.at[i,'TAG']} — {df.at[i,'Responsável']}"
            )

            with st.form("form_supervisor"):
                status       = st.selectbox("Novo Status", ["Enviado para Reforma", "Componente Entregue", "Cancelado"])
                rs           = st.text_input("Nº da RS")
                nota         = st.text_input("Nota Fiscal / Passe de saída")
                data_envio   = st.date_input("Data de Envio", datetime.date.today())
                data_entrega = None
                motivo       = ""
                if status == "Componente Entregue":
                    data_entrega = st.date_input("Data de Entrega", datetime.date.today())
                if status == "Cancelado":
                    motivo = st.text_area("Motivo do Cancelamento")
                submit_sup = st.form_submit_button("Salvar Atualização")

                if submit_sup:
                    df.at[idx, "Status"]              = status
                    df.at[idx, "RS"]                  = rs
                    df.at[idx, "Nota/Passe"]          = nota
                    df.at[idx, "Data_Envio"]          = str(data_envio)
                    df.at[idx, "Data_Entrega"]        = str(data_entrega) if data_entrega else ""
                    df.at[idx, "Cancelado"]           = "Sim" if status == "Cancelado" else "Não"
                    df.at[idx, "Motivo_Cancelamento"] = motivo
                    salvar_dados(df)
                    st.success("✅ Atualização salva com sucesso.")
        else:
            st.info("Nenhum componente pendente para atualizar.")
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
        st.success("Bem‑vindo, administrador.")
        st.markdown("### 📋 Todos os registros")
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

