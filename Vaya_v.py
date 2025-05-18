import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

# Archivos
DATA_FILE = "registro_data.pkl"
DEPOSITS_FILE = "registro_depositos.pkl"
DEBIT_NOTES_FILE = "registro_notas_debito.pkl"

st.set_page_config(page_title="Registro Proveedores y Depósitos", layout="wide")
st.title("Registro de Proveedores - Producto Pollo")

# Listas
proveedores = ["LIRIS SA", "Gallina 1", "Monze Anzules", "Medina"]
tipos_documento = ["Factura", "Nota de débito", "Nota de crédito"]
agencias = [
    "Cajero Automático Pichincha", "Cajero Automático Pacífico",
    "Cajero Automático Guayaquil", "Cajero Automático Bolivariano",
    "Banco Pichincha", "Banco del Pacifico", "Banco de Guayaquil",
    "Banco Bolivariano"
]

# Inicializar estados
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.data = pd.read_pickle(DATA_FILE)
        st.session_state.data["Fecha"] = pd.to_datetime(
            st.session_state.data["Fecha"], errors="coerce").dt.date
    else:
        st.session_state.data = pd.DataFrame(columns=[
            "Nº", "Fecha", "Proveedor", "Producto", "Cantidad",
            "Peso Salida (kg)", "Peso Entrada (kg)", "Tipo Documento",
            "Cantidad de gavetas", "Precio Unitario ($)", "Promedio",
            "Kilos Restantes", "Libras Restantes", "Total ($)",
            "Monto Depósito", "Saldo diario", "Saldo Acumulado"
        ])
        fila_inicial = {col: None for col in st.session_state.data.columns}
        fila_inicial["Saldo diario"] = 0.00
        fila_inicial["Saldo Acumulado"] = -35
        st.session_state.data = pd.concat(
            [pd.DataFrame([fila_inicial]), st.session_state.data], ignore_index=True
        )

if "df" not in st.session_state:
    if os.path.exists(DEPOSITS_FILE):
        st.session_state.df = pd.read_pickle(DEPOSITS_FILE)
        st.session_state.df["Fecha"] = pd.to_datetime(
            st.session_state.df["Fecha"], errors="coerce").dt.date
    else:
        st.session_state.df = pd.DataFrame(columns=[
            "Fecha", "Empresa", "Agencia", "Monto", "Documento", "N"
        ])

if "notas" not in st.session_state:
    if os.path.exists(DEBIT_NOTES_FILE):
        st.session_state.notas = pd.read_pickle(DEBIT_NOTES_FILE)
    else:
        st.session_state.notas = pd.DataFrame(columns=[
            "Fecha", "Libras calculadas", "Descuento", "Descuento posible", "Descuento real"
        ])

# Sidebar - Registro de Depósitos
st.sidebar.header("Registro de Depósitos")
with st.sidebar.form("registro_form"):
    fecha_d = st.date_input("Fecha del registro", value=datetime.today(), key="fecha_d")
    empresa = st.selectbox("Empresa (Proveedor)", proveedores, key="empresa")
    agencia = st.selectbox("Agencia", agencias, key="agencia")
    monto = st.number_input("Monto", min_value=0.0, format="%.2f", key="monto")
    submit_d = st.form_submit_button("Agregar Depósito")

if submit_d:
    documento = "Depósito" if "Cajero" in agencia else "Transferencia"
    df_actual = st.session_state.df
    coincidencia = df_actual[
        (df_actual["Fecha"] == fecha_d) & (df_actual["Empresa"] == empresa)
    ]
    numero = coincidencia["N"].iloc[0] if not coincidencia.empty else f"{df_actual['Fecha'].nunique() + 1:02}"

    nuevo_registro = {
        "Fecha": fecha_d,
        "Empresa": empresa,
        "Agencia": agencia,
        "Monto": monto,
        "Documento": documento,
        "N": numero
    }

    st.session_state.df = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
    st.session_state.df.to_pickle(DEPOSITS_FILE)
    st.success("Depósito agregado exitosamente.")

# Eliminar depósito
st.sidebar.subheader("Eliminar un Depósito")
if not st.session_state.df.empty:
    st.session_state.df["Mostrar"] = st.session_state.df.apply(
        lambda row: f"{row['Fecha']} - {row['Empresa']} - ${row['Monto']:.2f}", axis=1
    )
    deposito_a_eliminar = st.sidebar.selectbox(
        "Selecciona un depósito a eliminar", st.session_state.df["Mostrar"]
    )
    if st.sidebar.button("Eliminar depósito seleccionado"):
        index_eliminar = st.session_state.df[st.session_state.df["Mostrar"] == deposito_a_eliminar].index[0]
        st.session_state.df.drop(index=index_eliminar, inplace=True)
        st.session_state.df.reset_index(drop=True, inplace=True)
        st.session_state.df.to_pickle(DEPOSITS_FILE)
        st.sidebar.success("Depósito eliminado correctamente.")
else:
    st.sidebar.write("No hay depósitos para eliminar.")

# Registro de Proveedores
st.subheader("Registro de Proveedores")
with st.form("formulario"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fecha = st.date_input("Fecha", value=datetime.today())
        proveedor = st.selectbox("Proveedor", proveedores)
    with col2:
        cantidad = st.number_input("Cantidad", min_value=0, step=1)
        peso_salida = st.number_input("Peso Salida (kg)", min_value=0.0, step=0.1)
    with col3:
        peso_entrada = st.number_input("Peso Entrada (kg)", min_value=0.0, step=0.1)
        documento = st.selectbox("Tipo Documento", tipos_documento)
    with col4:
        gavetas = st.number_input("Cantidad de gavetas", min_value=0, step=1)
        precio_unitario = st.number_input("Precio Unitario ($)", min_value=0.0, step=0.01)

    enviar = st.form_submit_button("Agregar Registro")

if enviar:
    df = st.session_state.data.copy()
    producto = "Pollo"
    kilos_restantes = peso_salida - peso_entrada
    libras_restantes = kilos_restantes * 2.20462
    promedio = libras_restantes / cantidad if cantidad != 0 else 0
    total = libras_restantes * precio_unitario
    enumeracion = df["Fecha"].nunique() + 1 if fecha not in df["Fecha"].dropna().values else df[df["Fecha"] == fecha]["Nº"].iloc[0]

    nueva_fila = {
        "Nº": enumeracion,
        "Fecha": fecha,
        "Proveedor": proveedor,
        "Producto": producto,
        "Cantidad": cantidad,
        "Peso Salida (kg)": peso_salida,
        "Peso Entrada (kg)": peso_entrada,
        "Tipo Documento": documento,
        "Cantidad de gavetas": gavetas,
        "Precio Unitario ($)": precio_unitario,
        "Promedio": promedio,
        "Kilos Restantes": kilos_restantes,
        "Libras Restantes": libras_restantes,
        "Total ($)": total,
        "Monto Depósito": 0.0,
        "Saldo diario": 0.0,
        "Saldo Acumulado": 0.0
    }

    st.session_state.data = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    st.session_state.data.to_pickle(DATA_FILE)
    st.success("Registro agregado correctamente")

# Registro de Nota de Débito
st.subheader("Registro de Nota de Débito")
with st.form("nota_debito"):
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_nota = st.date_input("Fecha de Nota")
    with col2:
        descuento = st.number_input("Descuento (%)", min_value=0.0, max_value=1.0, step=0.01)
    with col3:
        descuento_real = st.number_input("Descuento Real ($)", min_value=0.0, step=0.01)
    agregar_nota = st.form_submit_button("Agregar Nota de Débito")

if agregar_nota:
    df = st.session_state.data.copy()
    libras_calculadas = df[df["Fecha"] == fecha_nota]["Libras Restantes"].sum()
    descuento_posible = libras_calculadas * descuento
    nueva_nota = {
        "Fecha": fecha_nota,
        "Libras calculadas": libras_calculadas,
        "Descuento": descuento,
        "Descuento posible": descuento_posible,
        "Descuento real": descuento_real
    }
    st.session_state.notas = pd.concat([st.session_state.notas, pd.DataFrame([nueva_nota])], ignore_index=True)
    st.session_state.notas.to_pickle(DEBIT_NOTES_FILE)
    st.success("Nota de débito agregada correctamente")

# Recalcular Monto Depósito, Saldo Diario y Saldo Acumulado
if not st.session_state.data.empty:
    df = st.session_state.data.copy()
    depositos = st.session_state.df.copy()
    notas = st.session_state.notas.copy()
    df = df.sort_values("Fecha").reset_index(drop=True)
    saldo_acumulado = -35

    for i, row in df.iterrows():
        fecha = row["Fecha"]
        proveedor = row["Proveedor"]
        total = row["Total ($)"] if pd.notna(row["Total ($)"]) else 0
        monto_deposito = depositos[
            (depositos["Fecha"] == fecha) & (depositos["Empresa"] == proveedor)
        ]["Monto"].sum()
        saldo_diario = monto_deposito - total
        descuento_total = notas[notas["Fecha"] <= fecha]["Descuento real"].sum()
        saldo_acumulado = saldo_acumulado + saldo_diario + descuento_total

        st.session_state.data.at[i, "Monto Depósito"] = monto_deposito
        st.session_state.data.at[i, "Saldo diario"] = saldo_diario
        st.session_state.data.at[i, "Saldo Acumulado"] = saldo_acumulado - descuento_total

# Mostrar tabla de registros
st.subheader("Tabla de Registros")
df_display = st.session_state.data.copy()
df_display["Saldo diario"] = df_display["Saldo diario"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
df_display["Saldo Acumulado"] = df_display["Saldo Acumulado"].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
st.dataframe(df_display, use_container_width=True)

# Eliminar fila de registro
st.subheader("Eliminar un Registro de la Tabla Principal")
if not st.session_state.data.empty:
    st.session_state.data["Mostrar"] = st.session_state.data.apply(
        lambda row: f"{row['Fecha']} - {row['Proveedor']} - ${row['Total ($)']:.2f}", axis=1
    )
    fila_a_eliminar = st.selectbox("Selecciona un registro para eliminar", st.session_state.data["Mostrar"])
    if st.button("Eliminar Registro Seleccionado"):
        index_eliminar = st.session_state.data[st.session_state.data["Mostrar"] == fila_a_eliminar].index[0]
        st.session_state.data.drop(index=index_eliminar, inplace=True)
        st.session_state.data.reset_index(drop=True, inplace=True)
        st.session_state.data.to_pickle(DATA_FILE)
        st.success("Registro eliminado correctamente.")

# Tabla de Notas de Débito
st.subheader("Tabla de Notas de Débito")
st.dataframe(st.session_state.notas.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)

# Eliminar Nota de Débito
st.subheader("Eliminar una Nota de Débito")
if not st.session_state.notas.empty:
    st.session_state.notas["Mostrar"] = st.session_state.notas.apply(
        lambda row: f"{row['Fecha']} - Libras: {row['Libras calculadas']:.2f} - Descuento real: ${row['Descuento real']:.2f}", axis=1
    )
    nota_a_eliminar = st.selectbox("Selecciona una nota para eliminar", st.session_state.notas["Mostrar"])
    if st.button("Eliminar Nota de Débito seleccionada"):
        index_eliminar = st.session_state.notas[st.session_state.notas["Mostrar"] == nota_a_eliminar].index[0]
        st.session_state.notas.drop(index=index_eliminar, inplace=True)
        st.session_state.notas.reset_index(drop=True, inplace=True)
        st.session_state.notas.to_pickle(DEBIT_NOTES_FILE)
        st.success("Nota de débito eliminada correctamente.")
else:
    st.write("No hay notas de débito para eliminar.")

# Descargar Excel
@st.cache_data
def convertir_excel(df):
    output = BytesIO()
    df_copy = df.copy()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_copy.to_excel(writer, index=False)
    output.seek(0)
    return output

st.download_button(
    label="Descargar Registros Excel",
    data=convertir_excel(st.session_state.data),
    file_name="registro_proveedores_depositos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

with st.expander("Ver depósitos registrados"):
    st.dataframe(st.session_state.df.drop(columns=["Mostrar"], errors="ignore"), use_container_width=True)
