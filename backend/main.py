from assistente.ambiente import registro
from assistente.rede import servidor

registro.configurar()
servidor.subir(servidor.montar_do_ambiente())
