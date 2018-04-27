CREATE TABLE core_empresassocias AS
	SELECT cnpj_empresa, nome_empresa, cpf_cnpj_socio AS cnpj_socia
	FROM core_sociosbrasil
	WHERE cpf_cnpj_socio IS NOT NULL;

CREATE INDEX idx_cnpj_socio ON core_empresassocias (cnpj_empresa, cnpj_socia, nome_empresa);

ALTER TABLE core_empresassocias ADD search_data tsvector;

ALTER TABLE core_empresassocias ADD id SERIAL PRIMARY KEY;
