## Matheus Braga

**AI Builder** · Engenharia de Computação na UFG (Goiânia)

Construo com IA soluções para problemas reais e coloco em produção: agentes, automações e sistemas internos,
do primeiro protótipo ao servidor. Portfólio: **[ia.matheusbragadev.com](https://ia.matheusbragadev.com)**

### Agora

- **Grupo Odilon Santos**, Laboratório 3D: bot de WhatsApp com 3 agentes de IA (n8n + OpenAI + Evolution API) que atende
  as garagens de ônibus, e o sistema interno por trás dele (catálogo, produção, custos e vitrine de vendas).
- **Iniciação Científica na UFG**: extração automática de faturas de água e energia de órgãos públicos para auditoria de consumo.

### Destaques

| Projeto | O que resolve | Resultado |
|---|---|---|
| **Bot do Laboratório 3D** *(privado, empresa)* | Funcionários pedem peças, reportam problemas com foto e acompanham pedidos pelo WhatsApp. Três agentes (triagem, pedido e ocorrência) com memória no Postgres, e passagem para um humano quando o assunto foge do escopo. | Em uso, testado por agentes Claude que simulam perfis de usuário |
| **[FindBus](https://findbus.com.br)** | Mostra em tempo real quais ônibus de Goiânia que estão chegando têm ar-condicionado. Cache em 3 camadas (Redis, Cloudflare, navegador). | 12,6 mil visitas por mês |
| **[Extração de faturas](https://github.com/MatheusBraga1106/extrator-faturas-agua)** | PDF de conta de água → dados estruturados, com OCR para documentos digitalizados e validação cruzada. | Suspeitas de erro de 217 → 63 em 9.820 faturas |
| **Monitor do mercado de confiança** *(privado)* | Geladeira sem atendente do Centro Acadêmico da UFG: câmera e sensores (ESP32-S3) e painel de auditoria. | Em uso desde out/2026 |
| **[Hub Sim Racing](https://github.com/MatheusBraga1106/hub-sim-racing)** | App desktop para equipamentos de simulação, com cena 3D. Feito com subagentes do Claude Code. | 670+ testes, 9 versões publicadas |
| **[3d-web-dev-skills](https://github.com/MatheusBraga1106/3d-web-dev-skills)** | Skill do Claude Code com o padrão de interfaces 3D servidas por Python. | Reutilizada em projetos novos |

### Como eu trabalho com IA

- **Claude Code como equipe:** especificação e plano primeiro, tarefas divididas entre subagentes, revisão a cada entrega.
- **Vários agentes, um projeto:** no estágio, o desenvolvimento é dividido entre 3 agentes do Claude (sistema, WhatsApp e coleta de dados), que se comunicam por contratos de API.
- **IA fora do chat:** integrações via MCP, como a do Fusion 360, em que o Claude modelou uma peça aprovada na primeira impressão.

### Stack

- **IA e automação:** n8n · OpenAI · Claude Code · MCP · Gemini · Evolution API · OCR (Tesseract)
- **Dados e backend:** Python · FastAPI · PostgreSQL · Supabase · pandas · SQL · Power BI
- **Infra:** Docker · Dokploy · VPS Linux · Cloudflare
- **Hardware:** ESP32 · Arduino · impressão 3D · Fusion 360

### Contato

[LinkedIn](https://www.linkedin.com/in/mmatheusbraga/) · mmatheusbragamed@gmail.com
