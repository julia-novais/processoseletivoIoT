
-
## Relatório do Candidato

### Identificação do Candidato

- **Nome completo:** Júlia Novais Pereira
- **GitHub:** https://github.com/julia-novais

---

## Visão Geral da Solução

**Objetivo do projeto:** O objetivo é criar uma solução embarcada para controle de qualidade e auditoria em ambientes refrigerados, estufas ou painéis elétricos, monitorando o tempo de exposição térmica e a integridade do isolamento físico para prevenir a degradação de insumos ou sobreaquecimento de componentes.

**Funcionamento do sistema:** O ESP32 monitora continuamente o estado da porta por meio de um botão, que simula sua abertura e fechamento, e realiza a leitura da temperatura utilizando o sensor MPU6050 via comunicação I2C. Caso a porta permaneça aberta por mais tempo que o permitido ou seja detectada uma variação significativa de temperatura, o sistema entra em estado de alerta. Assim que as condições voltam ao normal e permanecem estáveis por um determinado período, o alarme é desativado automaticamente.

**Interação com o usuário:** Toda a interação acontece no ambiente de simulação Wokwi. O botão representa a porta física, enquanto a temperatura pode ser alterada diretamente no sensor MPU6050 para simular diferentes cenários de funcionamento.
---

## Arquitetura do Sistema Embarcado

**Funcionamento do main.py:** Quando o programa inicia, ele configura os pinos, inicializa a comunicação I2C e exibe uma mensagem de inicialização. Depois disso, entra em um loop que fica verificando o estado da porta e a temperatura para decidir quando ativar ou desativar os alertas.

**Controle do tempo:** As verificações acontecem a cada 100 ms. Para controlar o tempo que a porta permanece aberta e o período necessário para voltar ao estado normal, foram utilizadas as funções time.ticks_ms() e time.ticks_diff().

**Comunicação entre os componentes:** O botão está ligado ao GPIO 14 e é usado para simular a porta. O sensor MPU6050 se comunica com o ESP32 via I2C, utilizando os pinos SDA (21) e SCL (22), enviando as informações de temperatura.
---

## Componentes Utilizados na Simulação

**ESP32 DevKit C V4:** responsável por executar toda a lógica do sistema.
**Botão:** utilizado para simular a abertura e o fechamento da porta.
**MPU6050:** usado para fazer a leitura da temperatura.

---

## Decisões Técnicas Relevantes

Durante o desenvolvimento, procurei manter o código organizado, separando a configuração dos periféricos da lógica principal do sistema. Os valores utilizados, como o tempo máximo para a porta permanecer aberta, o limite de variação de temperatura e o tempo de estabilização, foram definidos como constantes para facilitar futuras alterações.

Também utilizei um bloco try-except na leitura do sensor MPU6050 para evitar que possíveis falhas de comunicação interrompessem a execução do programa. Além disso, foi implementado um tempo de estabilidade antes de o sistema voltar ao estado normal, evitando que pequenas oscilações na temperatura ou mudanças rápidas no estado da porta gerassem alertas desnecessários.

---

## Resultados Obtidos

O sistema funcionou como esperado durante os testes. Foi possível identificar corretamente quando a porta permaneceu aberta por muito tempo e quando houve uma variação de temperatura acima do limite definido. Depois que a situação voltava ao normal, o sistema também retornava ao estado inicial sem problemas.

A simulação foi executada no Wokwi e todos os testes da esteira do GitHub Actions foram aprovados.
---

## Comentários Adicionais (Opcional)

**Dificuldades encontradas:** A maior dificuldade foi ajustar os tempos do sistema para atender aos testes automáticos sem prejudicar o funcionamento da lógica do projeto.

**Melhorias futuras:** Como melhoria, seria interessante adicionar comunicação via Wi-Fi para enviar alertas e informações do sistema em tempo real utilizando MQTT.
---

> Este relatório faz parte da avaliação técnica.  
> Clareza, objetividade e organização são tão importantes quanto o funcionamento do código.

