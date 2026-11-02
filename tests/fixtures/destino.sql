-- Esquema de teste baseado nos scripts unitários do modelo normalizado.
CREATE TABLE super_admin(
    id         BIGSERIAL PRIMARY KEY,
    nome       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    senha_hash      VARCHAR(255) NOT NULL,
    esta_ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE instituicao (
    id                 BIGSERIAL PRIMARY KEY,
    nome               VARCHAR(100) NOT NULL,
    tipo_instituicao   INTEGER NOT NULL,
    email_corporativo  VARCHAR(100) UNIQUE,
    dominio_email      VARCHAR(100) NOT NULL UNIQUE,
    data_criacao       TIMESTAMP NOT NULL DEFAULT NOW(),
    esta_ativo         BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_tipo_instituicao_1_a_4 CHECK (tipo_instituicao BETWEEN 1 AND 4)
);

CREATE TABLE plano(
    id            BIGSERIAL PRIMARY KEY,
    nome          VARCHAR(100) NOT NULL,
    valor         DECIMAL(10,2) NOT NULL,
    descricao     VARCHAR(255),
    duracao_meses INTEGER NOT NULL,
    data_criacao  TIMESTAMP NOT NULL DEFAULT NOW(),
    esta_ativo    BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_duracao_meses_positiva
        CHECK (duracao_meses > 0)
);

CREATE TABLE unidade(
    id             BIGSERIAL PRIMARY KEY,
    instituicao_id BIGINT NOT NULL REFERENCES instituicao(id),
    nome           VARCHAR(100) NOT NULL,
    cnpj           VARCHAR(14) NOT NULL UNIQUE,
    logradouro     VARCHAR(100) NOT NULL,
    numero         VARCHAR(10) NOT NULL,
    complemento    VARCHAR(100),
    bairro         VARCHAR(100) NOT NULL,
    cidade         VARCHAR(100) NOT NULL,
    estado         VARCHAR(2) NOT NULL,
    cep            VARCHAR(8) NOT NULL,
    data_criacao   TIMESTAMP NOT NULL DEFAULT NOW(),
    esta_ativo     BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE usuario (
    id               BIGSERIAL PRIMARY KEY,
    unidade_id      BIGINT NOT NULL REFERENCES unidade(id),
    nome_completo    VARCHAR(100) NOT NULL,
    email            VARCHAR(100) NOT NULL UNIQUE,
    tipo_acesso      INTEGER NOT NULL,
    senha_hash       VARCHAR(255) NOT NULL,
    cargo            VARCHAR(100) NOT NULL,
    data_nascimento  DATE NOT NULL,
    data_criacao     TIMESTAMP NOT NULL DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW(),
    esta_ativo       BOOLEAN NOT NULL DEFAULT FALSE,
    primeiro_acesso  BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_usuario_id_unidade UNIQUE (id, unidade_id),
    CONSTRAINT ck_tipo_acesso_usuario_1_a_4 CHECK (tipo_acesso BETWEEN 1 AND 4)
);

CREATE TABLE contrato (
    id            BIGSERIAL PRIMARY KEY,
    plano_id      BIGINT NOT NULL REFERENCES plano(id),
    unidade_id   BIGINT NOT NULL REFERENCES unidade(id),
    data_inicio   DATE NOT NULL DEFAULT CURRENT_DATE,
    data_fim      DATE NOT NULL,
    status        INTEGER NOT NULL DEFAULT 1,
    data_criacao  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_status_contrato_1_a_3 CHECK (status BETWEEN 1 AND 3),
    CONSTRAINT ck_data_fim_maior_data_inicio CHECK (data_fim > data_inicio)
);

CREATE TABLE pagamento (
    id                BIGSERIAL PRIMARY KEY,
    contrato_id       BIGINT NOT NULL REFERENCES contrato(id),
    data_pagamento    TIMESTAMP NOT NULL,
    valor_pago        DECIMAL(10, 2) NOT NULL,
    status            INTEGER DEFAULT 1,
    metodo_pagamento  INTEGER NOT NULL,
    data_criacao      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_status_pagamento_1_a_3 CHECK (status BETWEEN 1 AND 3),
    CONSTRAINT ck_metodo_pagamento_1_a_3 CHECK (metodo_pagamento BETWEEN 1 AND 3)
);

CREATE TABLE foto (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuario(id),
    url VARCHAR(255) NOT NULL,
    esta_ativo BOOLEAN NOT NULL DEFAULT TRUE,
    data_criacao TIMESTAMP NOT NULL DEFAULT NOW()
);
