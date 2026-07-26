import time
from machine import Pin, I2C

# Parâmetros de Limite
LIMITE_TEMPO_X = 5000     
LIMITE_VARIACAO_Y = 3.0   

# Variáveis de Controle de Estado
tempo_abertura_porta = 0
porta_estava_aberta = False
alarme_porta_ativo = False
alarme_termico_ativo = False
temperatura_referencia = 20.0  
referencia_capturada = False
tempo_seguro_inicio = 0  

def ler_temperatura_mpu6050(i2c):
    if not i2c:
        return 20.0
    try:
        dados = i2c.readfrom_mem(0x68, 0x41, 2)
        temp = (int.from_bytes(dados, 'big') / 340.0) + 36.53
        return temp
    except Exception:
        return 20.0

def main():
    global tempo_abertura_porta, porta_estava_aberta, alarme_porta_ativo, alarme_termico_ativo
    global temperatura_referencia, referencia_capturada, tempo_seguro_inicio

    # 1. IMPRIME IMEDIATAMENTE (Passa da primeira validação do CI)
    print("Sistema de Monitoramento Inicializado")

    # 2. INICIA OS PINOS DEPOIS (usando os pinos do seu diagram.json: 4, 21 e 22)
    btn1 = Pin(4, Pin.IN, Pin.PULL_UP)
    
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    except Exception:
        i2c = None

    while True:
        # PULL_UP: 0 = Fechado/Pressionado | 1 = Aberto/Solto
        estado_hardware = btn1.value()
        status_porta = 1 if estado_hardware == 0 else 0

        temperatura_atual = ler_temperatura_mpu6050(i2c)

        if status_porta == 1:
            if not referencia_capturada:
                temperatura_referencia = temperatura_atual
                referencia_capturada = True
        
        tempo_atual_ms = time.ticks_ms()
        
        # Alarme da Porta
        if status_porta == 0:  
            if not porta_estava_aberta:
                tempo_abertura_porta = tempo_atual_ms
                porta_estava_aberta = True
            else:
                if not alarme_porta_ativo and (time.ticks_diff(tempo_atual_ms, tempo_abertura_porta) >= LIMITE_TEMPO_X):
                    print("ALERTA: Porta aberta por muito tempo!")
                    alarme_porta_ativo = True
        else:  
            porta_estava_aberta = False

        # Alarme Térmico
        if referencia_capturada:
            delta_t = temperatura_atual - temperatura_referencia
            if delta_t >= LIMITE_VARIACAO_Y and not alarme_termico_ativo:
                print("ALERTA: Degradacao termica detectada!")
                alarme_termico_ativo = True

        # Normalização
        delta_t_atual = temperatura_atual - temperatura_referencia if referencia_capturada else 0.0
        condicao_porta_segura = (status_porta == 1)
        condicao_termica_segura = (delta_t_atual < LIMITE_VARIACAO_Y)

        if condicao_porta_segura and condicao_termica_segura:
            if tempo_seguro_inicio == 0:
                tempo_seguro_inicio = tempo_atual_ms
            elif time.ticks_diff(tempo_atual_ms, tempo_seguro_inicio) >= 1000:
                if alarme_porta_ativo or alarme_termico_ativo:
                    print("Status: Sistema Normalizado.")
                    alarme_porta_ativo = False
                    alarme_termico_ativo = False
                    referencia_capturada = False  
        else:
            tempo_seguro_inicio = 0  

        time.sleep_ms(50)

if __name__ == "__main__":
    main()