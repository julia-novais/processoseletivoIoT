import machine
import time

# ==========================================
# 1. PARAMETRIZAÇÃO DO SISTEMA
LIMITE_TEMPO_X = 5000       # 5 segundos exatos, conforme exigido pelo CI
LIMITE_VARIACAO_Y = 3.0     # Gradiente de 3 graus

# ==========================================
# 2. CONFIGURAÇÃO DE HARDWARE
# ==========================================
# Mantemos o PULL_DOWN (o diagrama JSON que alteramos com 3V3 está corretíssimo)
pino_porta = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Configuração I2C
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))

# Acorda o MPU6050 silenciosamente (Sem prints que possam quebrar o CI)
try:
    i2c.writeto_mem(0x68, 0x6B, b'\x00')
except OSError:
    pass

# Dá tempo para o sensor MPU6050 estabilizar na simulação
time.sleep_ms(100) 

def ler_temperatura():
    """Lê a temperatura e retorna None caso falhe, evitando o perigoso 0.0"""
    try:
        raw = i2c.readfrom_mem(0x68, 0x41, 2)
        val = raw[0] << 8 | raw[1]
        if val > 32767:
            val -= 65536
        return (val / 340.0) + 36.53
    except OSError:
        return None

# ==========================================
# 3. INICIALIZAÇÃO
# ==========================================
# 1ª MENSAGEM OBRIGATÓRIA (Tem que ser a primeira coisa a aparecer no console)
print("Sistema de Monitoramento Inicializado")

# Loop de segurança: Impede que a temperatura de referência inicialize bugada
temp_referencia = None
while temp_referencia is None:
    temp_referencia = ler_temperatura()
    if temp_referencia is None:
        time.sleep_ms(50)

tempo_inicio_abertura = 0
alarme_porta = False
alarme_temp = False
sistema_normal = True

# ==========================================
# 4. LAÇO PRINCIPAL (FIRMWARE)
# ==========================================
while True:
    estado_porta = pino_porta.value() # 0 = Aberto, 1 = Fechado
    porta_aberta = (estado_porta == 0)
    
    temp_atual = ler_temperatura()
    
    # Só executa as validações se a leitura do sensor não falhou
    if temp_atual is not None:
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

        # --- Lógica D: Normalização ---
        if not sistema_normal:
            if not porta_aberta and delta_t < LIMITE_VARIACAO_Y:
                alarme_porta = False
                alarme_temp = False
                sistema_normal = True
                
                # Reseta a temperatura de referência ao fechar a porta
                temp_referencia = temp_atual 
                
                print("Status: Sistema Normalizado.")
                
    # Delay não bloqueante
    time.sleep_ms(10)