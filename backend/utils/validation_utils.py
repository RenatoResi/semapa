def validar_campos_obrigatorios(data, campos):
    faltando = [campo for campo in campos if campo not in data or data[campo] in (None, '')]
    if faltando:
        raise ValueError(f"Campos obrigatórios ausentes: {', '.join(faltando)}")
