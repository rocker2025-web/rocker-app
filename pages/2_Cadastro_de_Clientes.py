# pages/2_Cadastro_de_Clientes.py
import streamlit as st
import utils
import uuid
import pandas as pd
from datetime import date

st.set_page_config(page_title="Gerenciamento de Clientes", layout="wide")

# --- VERIFICAÇÃO DE AUTENTICAÇÃO E LOGOUT ---
if not st.session_state.get('autenticado'):
    st.error("Acesso negado. Por favor, realize o login.")
    st.stop()

with st.sidebar:
    st.success(f"Bem-vindo, {st.session_state.get('nome_usuario')}!")
    if st.button("Logout"):
        st.session_state['autenticado'] = False
        for key in ['cep_pesquisado', 'endereco', 'bairro', 'cidade', 'estado']:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("1_Login.py")

st.title("Plataforma de Gerenciamento de Clientes")

# --- CONEXÃO COM BANCO DE DADOS DE CLIENTES ---
try:
    drive = utils.login_gdrive()
    clients_file = utils.get_database_file(drive, "clients.json")
    clientes_data = utils.read_data(clients_file)
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# --- BUSCA DE CLIENTES ---
st.subheader("Buscar Cliente por CPF/CNPJ")
cpf_cnpj_busca = st.text_input("Digite o CPF ou CNPJ para buscar (com ou sem pontuação)")
if cpf_cnpj_busca:
    busca_limpa = "".join(filter(str.isdigit, cpf_cnpj_busca))
    clientes_encontrados = []
    if busca_limpa:
        for c in clientes_data:
            doc_armazenado_limpo = "".join(filter(str.isdigit, c.get('cpf_cnpj', '')))
            if busca_limpa in doc_armazenado_limpo:
                clientes_encontrados.append(c)

    if clientes_encontrados:
        st.write(f"{len(clientes_encontrados)} cliente(s) encontrado(s):")
        # A busca agora usa o mesmo expander da lista principal
        for cliente in clientes_encontrados:
             with st.expander(f"**{cliente['nome_razao_social']}** - {cliente['cpf_cnpj']}"):
                st.markdown(f"**Tipo:** {cliente['tipo_pessoa']}")
                if cliente.get('data_nascimento'):
                    st.markdown(f"**Data de Nascimento:** {cliente['data_nascimento']}")
                st.markdown(f"**E-mail:** {cliente.get('email', 'N/A')}")
                st.markdown(f"**Telefone:** {cliente.get('telefone', 'N/A')}")
                st.markdown("---")
                st.markdown("##### Endereço")
                st.markdown(f"**CEP:** {cliente.get('cep', 'N/A')}")
                st.markdown(f"**Endereço:** {cliente.get('endereco', 'N/A')}")
                st.markdown(f"**Cidade/UF:** {cliente.get('cidade', 'N/A')} / {cliente.get('estado', 'N/A')}")
                
                if cliente.get('representante_legal'):
                    rep = cliente['representante_legal']
                    st.markdown("---")
                    st.markdown("##### Representante Legal")
                    st.markdown(f"**Nome:** {rep.get('nome', 'N/A')}")
                    st.markdown(f"**CPF:** {rep.get('cpf', 'N/A')}")
                    st.markdown(f"**Data de Nascimento:** {rep.get('data_nascimento', 'N/A')}")
                    st.markdown(f"**Contato:** {rep.get('telefone', 'N/A')} / {rep.get('email', 'N/A')}")
    else:
        st.info("Nenhum cliente encontrado com este CPF/CNPJ.")

st.markdown("---")

# --- SEÇÃO DE CADASTRO ---
st.subheader("Cadastrar Novo Cliente")

st.markdown("##### 1. Busque o Endereço (Opcional)")
col_cep1, col_cep2 = st.columns([1, 3])
with col_cep1:
    cep_lookup_input = st.text_input("Digite o CEP para buscar")
with col_cep2:
    if st.button("Buscar Endereço"):
        if cep_lookup_input:
            dados_cep = utils.consultar_cep(cep_lookup_input)
            if dados_cep:
                st.session_state.cep_pesquisado = dados_cep.get('cep', '')
                st.session_state.endereco = dados_cep.get('logradouro', '')
                st.session_state.bairro = dados_cep.get('bairro', '')
                st.session_state.cidade = dados_cep.get('localidade', '')
                st.session_state.estado = dados_cep.get('uf', '')
                st.success("Endereço encontrado!")
            else:
                st.error("CEP não encontrado ou inválido.")
        else:
            st.warning("Por favor, insira um CEP para buscar.")

with st.form("cadastro_cliente_form"):
    st.markdown("##### 2. Preencha os Dados do Cliente")
    tipo_pessoa = st.radio("Tipo de Pessoa", ["Pessoa Física", "Pessoa Jurídica"], horizontal=True)

    st.markdown("###### Dados do Cliente")
    col1, col2 = st.columns(2)
    with col1:
        nome_razao_social = st.text_input("Nome / Razão Social*")
        cpf_cnpj_input = st.text_input("CPF / CNPJ*")
    with col2:
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
    
    st.markdown("###### Endereço")
    cep = st.text_input("CEP", value=st.session_state.get('cep_pesquisado', ''))
    endereco = st.text_input("Endereço (Rua/Logradouro)", value=st.session_state.get('endereco', ''))
    
    col_end1, col_end2 = st.columns(2)
    with col_end1:
        numero = st.text_input("Número")
    with col_end2:
        bairro = st.text_input("Bairro", value=st.session_state.get('bairro', ''))

    col_cid, col_est = st.columns(2)
    with col_cid:
        cidade = st.text_input("Cidade", value=st.session_state.get('cidade', ''))
    with col_est:
        estado = st.text_input("Estado (UF)", value=st.session_state.get('estado', ''))
    
    data_nascimento_pf, representante_legal = None, None
    rep_nome, rep_cpf, rep_telefone, rep_email = "", "", "", ""
    rep_nascimento = date.today()

    if tipo_pessoa == "Pessoa Física":
        data_nascimento_pf = st.date_input("Data de Nascimento", min_value=date(1900, 1, 1), max_value=date.today())
    else:
        st.markdown("---")
        st.markdown("##### Dados do Representante Legal*")
        col_rep1, col_rep2 = st.columns(2)
        with col_rep1:
            rep_nome = st.text_input("Nome do Representante*")
            rep_cpf = st.text_input("CPF do Representante*")
        with col_rep2:
            rep_nascimento = st.date_input("Data de Nascimento do Representante", min_value=date(1900, 1, 1), max_value=date.today())
        
        col_rep3, col_rep4 = st.columns(2)
        with col_rep3:
            rep_telefone = st.text_input("Telefone do Representante")
        with col_rep4:
            rep_email = st.text_input("E-mail do Representante")

    submitted = st.form_submit_button("Salvar Cliente")

    if submitted:
        if not nome_razao_social or not cpf_cnpj_input:
            st.warning("Nome/Razão Social e CPF/CNPJ são obrigatórios.")
        elif tipo_pessoa == "Pessoa Jurídica" and (not rep_nome or not rep_cpf):
            st.warning("Para Pessoa Jurídica, o Nome e o CPF do Representante Legal são obrigatórios.")
        else:
            doc_formatado = utils.validar_e_formatar_cpf(cpf_cnpj_input) if tipo_pessoa == "Pessoa Física" else utils.validar_e_formatar_cnpj(cpf_cnpj_input)
            if not doc_formatado:
                st.error("CPF ou CNPJ do cliente inválido. Verifique a digitação.")
            else:
                endereco_completo = f"{endereco}, {numero}, {bairro}" if numero and bairro else endereco
                if any(c['cpf_cnpj'] == doc_formatado for c in clientes_data):
                    st.error("Este CPF/CNPJ já está cadastrado!")
                else:
                    if tipo_pessoa == "Pessoa Jurídica":
                        representante_legal = {"nome": rep_nome, "cpf": rep_cpf, "data_nascimento": str(rep_nascimento), "telefone": rep_telefone, "email": rep_email}
                    
                    novo_cliente = {
                        "id": str(uuid.uuid4()), "tipo_pessoa": tipo_pessoa, "nome_razao_social": nome_razao_social,
                        "cpf_cnpj": doc_formatado, "data_nascimento": str(data_nascimento_pf) if data_nascimento_pf else None,
                        "email": email, "telefone": telefone, "cep": cep, "cidade": cidade, "estado": estado,
                        "endereco": endereco_completo, "representante_legal": representante_legal
                    }
                    clientes_data.append(novo_cliente)
                    utils.write_data(clients_file, clientes_data)
                    st.success(f"Cliente '{nome_razao_social}' salvo com sucesso!")
                    
                    for key in ['cep_pesquisado', 'endereco', 'bairro', 'cidade', 'estado']:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

st.markdown("---")

# --- LISTA DE CLIENTES CADASTRADOS ---
st.subheader("Clientes Cadastrados")
if clientes_data:
    clientes_ordenados = sorted(clientes_data, key=lambda c: c['nome_razao_social'])
    for cliente in clientes_ordenados:
        with st.expander(f"**{cliente['nome_razao_social']}** - {cliente['cpf_cnpj']}"):
            st.markdown(f"**Tipo:** {cliente['tipo_pessoa']}")
            if cliente.get('data_nascimento'):
                st.markdown(f"**Data de Nascimento:** {cliente['data_nascimento']}")
            
            st.markdown(f"**E-mail:** {cliente.get('email', 'N/A')}")
            st.markdown(f"**Telefone:** {cliente.get('telefone', 'N/A')}")
            
            st.markdown("---")
            st.markdown("##### Endereço")
            st.markdown(f"**CEP:** {cliente.get('cep', 'N/A')}")
            st.markdown(f"**Endereço:** {cliente.get('endereco', 'N/A')}")
            st.markdown(f"**Cidade/UF:** {cliente.get('cidade', 'N/A')} / {cliente.get('estado', 'N/A')}")
            
            if cliente.get('representante_legal'):
                rep = cliente['representante_legal']
                st.markdown("---")
                st.markdown("##### Representante Legal")
                st.markdown(f"**Nome:** {rep.get('nome', 'N/A')}")
                st.markdown(f"**CPF:** {rep.get('cpf', 'N/A')}")
                st.markdown(f"**Data de Nascimento:** {rep.get('data_nascimento', 'N/A')}")
                st.markdown(f"**Contato:** {rep.get('telefone', 'N/A')} / {rep.get('email', 'N/A')}")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.button("Editar Cliente", key=f"edit_{cliente['id']}", use_container_width=True)
            with col2:
                st.button("Excluir Cliente", key=f"delete_{cliente['id']}", use_container_width=True, type="primary")
else:
    st.info("Nenhum cliente cadastrado ainda.")

utils.exibir_rodape()