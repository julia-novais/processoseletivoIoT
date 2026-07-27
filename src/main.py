import machine
import time

# ==========================================
# 1. PARAMETRIZAÇÃO DO SISTEMA
# ==========================================
LIMITE_TEMPO_X = 5000       # 5 segundos exatos para o CI
LIMITE_VARIACAO_Y = 3.0     # Gradiente de 3 graus
TEMPO_ESTABILIZACAO = 1000  # 1 segundo de segurança para normalização

# ==========================================
# 2. CONFIGURAÇÃO DE HARDWARE
# ==========================================
pino_porta = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_DOWN)
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))

# Acorda o MPU6050 silenciosamente
try:
    i2c.writeto_mem(0x68, 0x6B, b'\x00')
except OSError:
    pass

# Atraso inicial para o simulador Wokwi inicializar os componentes
time.sleep_ms(200) 

def ler_temperatura():
    """Lê a temperatura e retorna 20.0°C como fallback caso o I2C falhe temporariamente"""
    try:
        raw = i2c.readfrom_mem(0x68, 0x41, 2)
        val = raw[0] << 8 | raw[1]
        if val > 32767:
            val -= 65536
        return (val / 340.0) + 36.53
    except OSError:
        return 20.0 

# ==========================================
# 3. INICIALIZAÇÃO OBRIGATÓRIA
# ==========================================
print("Sistema de Monitoramento Inicializado")

temp_referencia = ler_temperatura()

# Variáveis de controle de tempo
tempo_inicio_abertura = 0
tempo_inicio_seguranca = 0

# Variáveis de estado
alarme_porta = False
alarme_temp = False
sistema_normal = True

# ==========================================
# 4. LAÇO PRINCIPAL
# ==========================================
while True:
    estado_porta = pino_porta.value() # 0 = Aberto, 1 = Fechado
    porta_aberta = (estado_porta == 0)
    
    temp_atual = ler_temperatura()
    delta_t = temp_atual - temp_referencia
    
    # --- Lógica B: Tempo de Porta Aberta ---
    if porta_aberta:
        if tempo_inicio_abertura == 0:
            tempo_inicio_abertura = time.ticks_ms()
        else:
            tempo_decorrido = time.ticks_diff(time.ticks_ms(), tempo_inicio_abertura)
            if tempo_decorrido >= LIMITE_TEMPO_X and not alarme_porta:
                alarme_porta = True
                print("ALERTA: Porta aberta por muito tempo!")
    else:
        tempo_inicio_abertura = 0

    # --- Lógica C: Elevação Térmica ---
    if delta_t >= LIMITE_VARIACAO_Y:
        if not alarme_temp:
            alarme_temp = True
            print("ALERTA: Degradacao termica detectada!")
            
    # --- Atualização do Status Geral ---
    if alarme_porta or alarme_temp:
        sistema_normal = False

    # --- Lógica D: Normalização com Estabilização ---
    if not sistema_normal:
        # Verifica se as condições estão seguras
        if not porta_aberta and delta_t < LIMITE_VARIACAO_Y:
            if tempo_inicio_seguranca == 0:
                # Inicia o cronômetro de estabilização
                tempo_inicio_seguranca = time.ticks_ms()
            else:
                tempo_seguro_decorrido = time.ticks_diff(time.ticks_ms(), tempo_inicio_seguranca)
                
                # Só normaliza se permaneceu seguro pelo tempo estipulado
                if tempo_seguro_decorrido >= TEMPO_ESTABILIZACAO:
                    alarme_porta = False
                    alarme_temp = False
                    sistema_normal = True
                    
                    temp_referencia = temp_atual 
                    tempo_inicio_seguranca = 0 # Reseta o cronômetro
                    
                    print("Status: Sistema Normalizado.")
        else:
            # Se voltar a ficar inseguro antes de 1000ms, reseta o cronômetro de segurança
            tempo_inicio_seguranca = 0
            
    # Delay não bloqueante para sincronia da CPU do CI
    time.sleep_ms(20)