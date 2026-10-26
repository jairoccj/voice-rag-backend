"""Insert fictitious Tribunal de Contas demo documents into local pgvector."""
from dotenv import load_dotenv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.services.rag import rag_service


documentos_teste = [
    "Este conjunto contém informações fictícias para demonstração sobre a empresa Tribunal de Contas; não representa informação oficial do TCE-PB.",
    "O Tribunal de Contas do Estado da Paraíba (TCE-PB) funciona de segunda a sexta-feira, das 07h às 13h.",
    "Para estagiários no TCE-PB, a carga horária diária é de 4 horas, totalizando 20 horas semanais.",
    
    "O refeitório do Tribunal está aberto diariamente das 08h às 12h, oferecendo opções de lanches e refeições subsidiadas para servidores e estagiários.",
    "O código de vestimenta do Tribunal exige traje esporte fino; é proibida a entrada nas dependências utilizando bermudas, regatas ou chinelos.",
    "O estacionamento interno é de uso exclusivo para servidores efetivos e comissionados. Estagiários e visitantes devem utilizar o bolsão externo.",
    "A Biblioteca Conselheiro Fictício da Silva funciona no térreo do Bloco A, oferecendo acervo jurídico e acesso a computadores para pesquisa documental.",
    "O uso do crachá de identificação é obrigatório e ostensivo durante todo o período de permanência nas dependências do Tribunal.",
    "Os ramais de emergência interna são: Segurança (Ramal 9999), Brigada de Incêndio (Ramal 9998) e Serviço Médico (Ramal 9997).",
    
    "A Diretoria de Tecnologia da Informação (DTI) está localizada no 3º andar do Bloco B e é responsável pela manutenção dos sistemas corporativos e infraestrutura de rede.",
    "Para abertura de chamados técnicos, como problemas de rede, erro em sistemas ou falhas de hardware, o usuário deve acessar o Portal GLPI utilizando sua matrícula e senha de rede.",
    "O sistema principal de tramitação de processos internos é o e-TCE, sendo obrigatório para a abertura de qualquer chamado administrativo ou protocolo de ofícios.",
    "Todos os servidores e estagiários devem realizar o curso obrigatório de Segurança da Informação e Lei Geral de Proteção de Dados (LGPD) disponibilizado na plataforma EAD da DTI.",
    "O acesso remoto aos sistemas do Tribunal via VPN é restrito a servidores efetivos e requer autorização prévia da diretoria imediata.",
    
    "Estagiários têm direito a um recesso remunerado de 30 dias a cada um ano de estágio completo, preferencialmente tirado durante as férias escolares.",
    "A avaliação de desempenho dos estagiários ocorre a cada seis meses, sendo um requisito obrigatório para a renovação do termo de compromisso de estágio.",
    "O pagamento da bolsa-auxílio dos estagiários é processado pela folha de pagamento e realizado sempre até o 5º dia útil de cada mês, mediante depósito em conta bancária.",
    "O sistema de registro de ponto é biométrico. Os estagiários possuem uma tolerância de atraso de até 15 minutos por dia, sem desconto no valor da bolsa.",
    "Faltas por motivos de saúde devem ser obrigatoriamente justificadas mediante a apresentação de atestado médico à Divisão de Recursos Humanos (DRH) em até 48 horas após a ausência.",
    "Em caso de perda do crachá, o servidor ou estagiário deve solicitar a segunda via imediatamente na Divisão de Segurança, mediante pagamento de taxa administrativa de R$ 25,00.",
    
    "A Sessão Plenária, onde os conselheiros julgam as contas públicas dos municípios e do estado, ocorre todas as quartas-feiras a partir das 09h e é transmitida ao vivo pelo canal oficial.",
    "A central de atendimento ao jurisdicionado funciona no Bloco A e oferece suporte presencial para prefeitos e gestores públicos sobre a emissão de certidões negativas.",
    "O Serviço Médico e Odontológico do Tribunal atua de forma preventiva e está localizado no anexo C, com agendamentos realizados exclusivamente pela intranet.",
    "O Tribunal realiza anualmente a 'Semana de Inovação em Gestão Pública', um evento que ocorre na segunda quinzena de novembro com palestras e workshops abertos ao público externo."
]


def main():
    print("Inserindo documentos de teste no PostgreSQL...")
    for doc in documentos_teste:
        inserted = rag_service.add_document(doc)
        status = "inserido" if inserted else "já existia"
        print(f"Documento {status}: {doc[:30]}...")
    print("Concluído!")


if __name__ == "__main__":
    main()
