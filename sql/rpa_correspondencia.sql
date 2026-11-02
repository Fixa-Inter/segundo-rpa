-- TABELA: rpa_correspondencia
-- Descrição: Liga o ID de cada cadastro legado ao ID gerado no normalizado.
-- Dependências: tabelas de destino verificadas pelo RPA antes do commit.
CREATE TABLE IF NOT EXISTS public.rpa_correspondencia (
    origem TEXT NOT NULL,
    tabela TEXT NOT NULL,
    id_origem BIGINT NOT NULL,
    id_destino BIGINT NOT NULL,
    data_criacao TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (origem, tabela, id_origem),
    UNIQUE (origem, tabela, id_destino)
);
COMMENT ON TABLE public.rpa_correspondencia IS
'Controle permanente da sincronização. Não apagar entre execuções nem junto dos artifacts.';
