import time
from machine import Pin, I2C

btn1 = Pin(4, Pin.IN, Pin.PULL_UP)
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

LIMITE_TEMPO_X = 5000     
LIMITE_VARIACAO_Y = 3.0   

tempo_abertura_porta = 0
porta_estava_aberta = False
alarme_porta_ativo = False
alarme_termico_ativo = False

temperatura_referencia = 20.0  
referencia_capturada = False
tempo_seguro_inicio = 0  

def ler_temperatura_mpu6050():
    try:
        dados = i2c.readfrom_mem(0x68, 0x41, 2)
        temp = (int.from_bytes(dados, 'big') / 340.0) + 36.53
        return temp
    except Exception:
        return 20.0

def main():
    global tempo_abertura_porta, porta_estava_aberta, alarme_porta_ativo, alarme_termico_ativo
    global temperatura_referencia, referencia_capturada, tempo_seguro_inicio

    print("Sistema de Monitoramento Inicializado")

    while True:
        estado_hardware = btn1.value()
        status_porta = 1 if estado_hardware == 0 else 0

        temperatura_atual = ler_temperatura_mpu6050()

        if status_porta == 1:
            if not referencia_capturada:
                temperatura_referencia = temperatura_atual
                referencia_capturada = True
        
        tempo_atual_ms = time.ticks_ms()
        
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

        if referencia_capturada:
            delta_t = temperatura_atual - temperatura_referencia
            if delta_t >= LIMITE_VARIACAO_Y and not alarme_termico_ativo:
                print("ALERTA: Degradacao termica detectada!")
                alarme_termico_ativo = True

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

        time.sleep_ms(100)

if __name__ == "__main__":
    main()