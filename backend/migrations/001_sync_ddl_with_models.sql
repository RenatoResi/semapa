-- Migração: Sincronizar DDL com Modelos SQLAlchemy
-- Data: 2026-03-03
-- Alterações:
-- 1. Corrigir tipo de 'ativo' em users (String -> Boolean)
-- 2. Adicionar tabela 'tarefas' que está faltando

-- 1. CORRIGIR TABELA USERS
-- Remaneiar a coluna ativo como string se necessário
ALTER TABLE users ADD COLUMN ativo_temp boolean DEFAULT true;
UPDATE users SET ativo_temp = CASE WHEN ativo = 'True' THEN true ELSE false END;
ALTER TABLE users DROP COLUMN ativo;
ALTER TABLE users RENAME COLUMN ativo_temp TO ativo;
ALTER TABLE users ALTER COLUMN ativo SET DEFAULT true;
ALTER TABLE users ALTER COLUMN ativo SET NOT NULL;

-- 2. CRIAR TABELA TAREFAS (faltava no DDL)
CREATE TABLE IF NOT EXISTS public.tarefas (
    id serial4 NOT NULL,
    descricao text NOT NULL,
    requerimento_id int4 NULL,
    endereco varchar(100) NULL,
    bairro varchar(100) NULL,
    latitude varchar(20) NULL,
    longitude varchar(20) NULL,
    data_prevista date NOT NULL,
    periodo varchar(20) NULL,
    complexidade varchar(30) DEFAULT '3 - caminhao rapido' NULL,
    prioridade varchar(20) DEFAULT 'normal' NULL,
    status varchar(30) DEFAULT 'planejada' NULL,
    observacoes text NULL,
    chefe_equipe_id int4 NULL,
    criada_por int4 NOT NULL,
    criada_em timestamp DEFAULT CURRENT_TIMESTAMP NULL,
    atualizada_por int4 NOT NULL,
    atualizada_em timestamp DEFAULT CURRENT_TIMESTAMP NULL,
    concluida_em timestamp NULL,
    reagendada int4 DEFAULT 0 NULL,
    CONSTRAINT tarefas_pkey PRIMARY KEY (id),
    CONSTRAINT tarefas_requerimento_id_fkey FOREIGN KEY (requerimento_id) REFERENCES public.requerimentos(id) ON DELETE SET NULL,
    CONSTRAINT tarefas_chefe_equipe_id_fkey FOREIGN KEY (chefe_equipe_id) REFERENCES public.users(id),
    CONSTRAINT tarefas_criada_por_fkey FOREIGN KEY (criada_por) REFERENCES public.users(id),
    CONSTRAINT tarefas_atualizada_por_fkey FOREIGN KEY (atualizada_por) REFERENCES public.users(id)
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_tarefas_requerimento_id ON tarefas(requerimento_id);
CREATE INDEX IF NOT EXISTS idx_tarefas_status ON tarefas(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_data_prevista ON tarefas(data_prevista);
