CREATE TABLE core_empresassocias AS
	SELECT
		cnpj_empresa,
		nome_empresa,
		cpf_cnpj_socio AS cnpj_socia,
		qualificacao_socio AS qualificacao_socia,
		nome_socio AS nome_socia
	FROM core_sociosbrasil
	WHERE cpf_cnpj_socio IS NOT NULL;

CREATE INDEX idx_empresassocias_cnpj_socia ON core_empresassocias (cnpj_empresa, cnpj_socia, nome_empresa, qualificacao_socia);
CREATE INDEX idx_empresassocias_qualificacao_socia ON core_empresassocias (qualificacao_socia);

ALTER TABLE core_empresassocias ADD search_data tsvector;

ALTER TABLE core_empresassocias ADD id SERIAL PRIMARY KEY;
