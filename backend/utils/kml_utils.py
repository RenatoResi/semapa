from simplekml import Kml

def gerar_kml_arvores(arvores, caminho_kml):
    kml = Kml(name="Árvores SEMAPA", open=1)
    for a in arvores:
        ponto = kml.newpoint(
            name=a.especie,
            coords=[(float(a.longitude), float(a.latitude))]
        )
        ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
        ponto.description = f"""
            <![CDATA[
                <h3>Detalhes da Árvore</h3>
                <p>ID: {a.id}</p>
                <p>Espécie: {a.especie}</p>
            ]]>
        """
    kml.save(caminho_kml)
    return caminho_kml

def gerar_kml_arvore(arvore, caminho_kml):
    kml = Kml(name=f"Árvore {arvore.especie}", open=1)
    ponto = kml.newpoint(
        name=arvore.especie,
        coords=[(float(arvore.longitude), float(arvore.latitude))]
    )
    ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
    ponto.description = f"""
        <![CDATA[
            <h3>Detalhes da Árvore</h3>
            <p>ID: {arvore.id}</p>
            <p>Espécie: {arvore.especie}</p>
            <p>Endereço: {arvore.endereco}</p>
        ]]>
    """
    kml.save(caminho_kml)
    return caminho_kml
