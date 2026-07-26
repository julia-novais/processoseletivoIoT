import time
from machine import Pin, I2C


LIMITE_TEMPO_X = 3000     
LIMITE_VARIACAO_Y = 3.0   


btn1 = Pin(4, Pin.IN, Pin.PULL_UP)
try:
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
except Exception:
    i2c = None

def ler_temperatura():
    if not i2c: 
        return 20.0
    try:
        dados = i2c.readfrom_mem(0x68, 0x41, 2)
        temp = (int.from_bytes(dados, 'big') / 340.0) + 36.53
        return temp
    except Exception:
        return 20.0

def main():
    print("Sistema de Monitoramento Inicializado")

    tempo_abertura_porta = 0
    alarme_porta_ativo = False
    alarme_termico_ativo = False

    temperatura_referencia = 20.0  
    referencia_capturada = False
    tempo_seguro_inicio = 0  

    # Variáveis do Anti-Ruído (Debounce)
    ultimo_estado_raw = -1
    ultimo_tempo_debounce = 0
    status_porta = 1 # Assume porta fechada no início

    while True:
        agora = time.ticks_ms()

        # --- FILTRO ANTI-RUÍDO (DEBOUNCE) ---
        estado_raw = 1 if btn1.value() == 0 else 0
        if estado_raw != ultimo_estado_raw:
            ultimo_tempo_debounce = agora
            ultimo_estado_raw = estado_raw
        
        # Só aceita a mudança se o botão ficar estável por mais de 50ms
        if time.ticks_diff(agora, ultimo_tempo_debounce) > 50:
            status_porta = estado_raw

        # --- LEITURA TÉRMICA ---
        temp_atual = ler_temperatura()

        if status_porta == 1 and not referencia_capturada:
            temperatura_referencia = temp_atual
            referencia_capturada = True
        
        # --- ALARME DA PORTA ---
        if status_porta == 0:  
            if tempo_abertura_porta == 0:
                tempo_abertura_porta = agora
            else:
                if not alarme_porta_ativo and (time.ticks_diff(agora, tempo_abertura_porta) >= LIMITE_TEMPO_X):
                    print("ALERTA: Porta aberta por muito tempo!")
                    alarme_porta_ativo = True
        else:  
            tempo_abertura_porta = 0

        # --- ALARME TÉRMICO ---
        if referencia_capturada:
            delta_t = temp_atual - temperatura_referencia
            if delta_t >= LIMITE_VARIACAO_Y and not alarme_termico_ativo:
                print("ALERTA: Degradacao termica detectada!")
                alarme_termico_ativo = True

            # --- NORMALIZAÇÃO ---
            condicao_porta_segura = (status_porta == 1)
            condicao_termica_segura = (delta_t < LIMITE_VARIACAO_Y)

            if condicao_porta_segura and condicao_termica_segura:
                if tempo_seguro_inicio == 0:
                    tempo_seguro_inicio = agora
                elif time.ticks_diff(agora, tempo_seguro_inicio) >= 1000:
                    if alarme_porta_ativo or alarme_termico_ativo:
                        print("Status: Sistema Normalizado.")
                        alarme_porta_ativo = False
                        alarme_termico_ativo = False
                        referencia_capturada = False  
            else:
                tempo_seguro_inicio = 0  

        time.sleep_ms(20)

if __name__ == "__main__":
    main()