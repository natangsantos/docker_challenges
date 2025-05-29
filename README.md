# CTFd Docker Container Manager Plugin

Este plugin permite que administradores do CTFd configurem desafios que iniciam automaticamente contêineres Docker isolados quando um competidor começa a resolvê-los.

## Funcionalidades

*   **Tipo de Desafio Personalizado:** Introduz um novo tipo de desafio "docker".
*   **Gerenciamento de Instâncias:** Inicia um contêiner Docker dedicado por usuário/equipe para desafios específicos.
*   **Configuração Flexível:** Permite definir a imagem Docker, mapeamento de portas, variáveis de ambiente, limites de CPU/memória e tempo de expiração por desafio.
*   **Exibição de Conexão:** Mostra as informações de conexão (IP/Porta) necessárias para o competidor acessar a instância do desafio.
*   **Integração com Admin:** Adiciona opções de configuração na interface de criação/edição de desafios para o tipo "docker".
*   **API:** Fornece um endpoint de API para iniciar as instâncias a partir da visualização do desafio.

## Instalação

1.  **Copiar Plugin:** Copie a pasta `ctfd_docker_manager` inteira para o diretório `CTFd/plugins/` da sua instalação do CTFd.
2.  **Instalar Dependências:** Certifique-se de que o ambiente Python do seu CTFd tenha a biblioteca `docker` instalada. Você pode instalar as dependências do plugin executando:
    ```bash
    pip install -r /path/to/CTFd/plugins/ctfd_docker_manager/requirements.txt
    # Ou, se estiver usando o requirements.txt principal do CTFd:
    pip install docker
    ```
3.  **Reiniciar CTFd:** Reinicie o serviço do CTFd para que ele reconheça e carregue o novo plugin.
4.  **Configurar Docker:** Garanta que o serviço do CTFd tenha permissão para se comunicar com o daemon Docker (seja via socket Unix `/var/run/docker.sock` ou um endpoint TCP). A forma mais comum é adicionar o usuário que executa o CTFd ao grupo `docker`:
    ```bash
    sudo usermod -aG docker <usuario_ctfd>
    # Pode ser necessário reiniciar a sessão ou o sistema para que a alteração de grupo tenha efeito.
    ```
    *Alternativamente, configure a variável de ambiente `DOCKER_HOST` ou use a página de configuração do plugin (ainda em desenvolvimento) para especificar um host Docker diferente.*

## Uso

1.  **Criar Desafio:**
    *   Vá para o painel de administração do CTFd.
    *   Clique em "Challenges" e depois em "New Challenge".
    *   Selecione "docker" como o tipo de desafio.
    *   Preencha os campos padrão do desafio (nome, descrição, valor, categoria).
    *   Na seção de opções do tipo de desafio:
        *   **Docker Image:** Especifique a imagem Docker a ser usada (obrigatório).
        *   **Ports Mapping:** Defina os mapeamentos de porta (opcional, ex: `80/tcp:8080`).
        *   **Environment Variables:** Defina variáveis de ambiente (opcional, ex: `FLAG=flag{...}`).
        *   **CPU/Memory Limit:** Defina limites de recursos (opcional).
        *   **Instance Timeout:** Defina o tempo de vida da instância em segundos (opcional, padrão 3600).
    *   Adicione as flags corretas.
    *   Salve o desafio.

2.  **Resolver Desafio (Competidor):**
    *   Navegue até o desafio na interface do CTFd.
    *   Clique no botão "Start Instance".
    *   O plugin iniciará um contêiner Docker em segundo plano.
    *   As informações de conexão (e.g., `IP:Porta`) serão exibidas abaixo do botão.
    *   Use essas informações para se conectar à instância e resolver o desafio.
    *   Submeta a flag encontrada.

## Limitações e Próximos Passos

*   **Gerenciamento de Timeout:** A lógica para parar automaticamente os contêineres após o timeout ainda precisa ser implementada (requer um agendador ou processo em segundo plano).
*   **Gerenciamento de Estado:** Atualmente, não há verificação se uma instância já está em execução para o usuário/desafio antes de tentar iniciar uma nova (a implementação atual para e remove a antiga).
*   **Limpeza:** A limpeza automática de contêineres (em caso de erro, logout, etc.) pode ser aprimorada.
*   **Página de Configuração:** A página de configuração do administrador (`/admin/plugins/ctfd_docker_manager`) é um placeholder e precisa ser implementada para permitir configurações globais (host Docker, timeouts padrão, etc.).
*   **Segurança:** A configuração de rede e isolamento pode ser reforçada.
*   **Testes:** Testes automatizados precisam ser escritos.

## Dependências

*   Python 3
*   CTFd
*   Docker SDK for Python (`docker`)

