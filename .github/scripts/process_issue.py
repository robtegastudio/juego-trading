import json
import os
import sys
import requests
from datetime import datetime

def main():
    issue_title = os.environ['ISSUE_TITLE']
    issue_number = os.environ['ISSUE_NUMBER']
    github_token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']

    partes = issue_title.split(':')
    tipo = partes[0]

    users_file = 'users.json'
    if os.path.exists(users_file):
        with open(users_file) as f:
            users = json.load(f)
    else:
        users = {}

    def usuario_default():
        return {
            'saldoUSDT': 1000,
            'btc': 0,
            'tarjetas': [],
            'movimientos': [],
            'bloqueado': False,
            'rol': 'user'
        }

    def comment(msg):
        url = f'https://api.github.com/repos/{repo}/issues/{issue_number}/comments'
        headers = {'Authorization': f'token {github_token}'}
        requests.post(url, json={'body': msg}, headers=headers)

    if tipo == 'REGISTER':
        _, usuario, password = partes
        if usuario in users:
            comment('❌ El usuario ya existe')
        else:
            users[usuario] = usuario_default()
            users[usuario]['password'] = password
            comment(f'✅ Usuario {usuario} registrado correctamente')

    elif tipo == 'TRANSFER':
        _, origen, destino, monto_str = partes
        monto = float(monto_str)
        if origen not in users or destino not in users:
            comment('❌ Usuario origen o destino no existe')
        elif users[origen].get('bloqueado', False):
            comment('❌ Usuario origen bloqueado')
        elif users[origen]['saldoUSDT'] < monto:
            comment('❌ Saldo insuficiente')
        else:
            users[origen]['saldoUSDT'] -= monto
            users[destino]['saldoUSDT'] += monto
            users[origen]['movimientos'].append({
                'tipo': 'transferencia_enviada',
                'destino': destino,
                'monto': monto,
                'fecha': datetime.now().isoformat()
            })
            users[destino]['movimientos'].append({
                'tipo': 'transferencia_recibida',
                'origen': origen,
                'monto': monto,
                'fecha': datetime.now().isoformat()
            })
            comment(f'✅ Transferencia de {monto} USDT de {origen} a {destino} completada')

    elif tipo == 'ADMIN':
        accion = partes[1]
        if accion == 'SET_SALDO':
            _, _, objetivo, monto_str = partes
            monto = float(monto_str)
            if objetivo in users:
                users[objetivo]['saldoUSDT'] = monto
                comment(f'✅ Saldo de {objetivo} fijado en {monto} USDT')
            else:
                comment('❌ Usuario no existe')
        elif accion == 'BLOQUEAR':
            _, _, objetivo = partes
            if objetivo in users:
                users[objetivo]['bloqueado'] = True
                comment(f'✅ Usuario {objetivo} bloqueado')
            else:
                comment('❌ Usuario no existe')
        elif accion == 'DESBLOQUEAR':
            _, _, objetivo = partes
            if objetivo in users:
                users[objetivo]['bloqueado'] = False
                comment(f'✅ Usuario {objetivo} desbloqueado')
        elif accion == 'SET_PRECIO':
            _, _, precio_str = partes
            precio = float(precio_str)
            price_file = 'prices.json'
            if os.path.exists(price_file):
                with open(price_file) as f:
                    prices = json.load(f)
            else:
                prices = {'BTC': {'precio': 50000, 'timestamp': 0}}
            prices['BTC']['precio'] = precio
            prices['BTC']['timestamp'] = datetime.now().timestamp()
            with open(price_file, 'w') as f:
                json.dump(prices, f, indent=2)
            comment(f'✅ Precio BTC fijado en {precio} USDT')
        elif accion == 'ENVIAR_TARJETA':
            _, _, objetivo, tipo_tarjeta = partes
            if objetivo not in users:
                comment('❌ Usuario no existe')
                return
            # Generar datos de tarjeta ficticios
            import random
            num = f'{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}'
            ultimos4 = num[-4:]
            cvv = f'{random.randint(100,999)}'
            mes = random.randint(1,12)
            anio = random.randint(2025,2030)
            color1, color2 = {
                'bronce': ('#cd7f32', '#b06d2e'),
                'plata': ('#c0c0c0', '#a0a0a0'),
                'oro': ('#ffd700', '#e5c100'),
                'platino': ('#e5e4e2', '#c0c0c0'),
                'negro': ('#2c2c2c', '#1a1a1a')
            }.get(tipo_tarjeta, ('#667eea', '#764ba2'))
            tarjeta = {
                'tipo': tipo_tarjeta,
                'numero': num,
                'ultimos4': ultimos4,
                'cvv': cvv,
                'mes': mes,
                'anio': anio,
                'color1': color1,
                'color2': color2
            }
            if 'tarjetas' not in users[objetivo]:
                users[objetivo]['tarjetas'] = []
            users[objetivo]['tarjetas'].append(tarjeta)
            comment(f'✅ Tarjeta {tipo_tarjeta} enviada a {objetivo}')
        # Puedes añadir más comandos admin aquí

    elif tipo == 'JUEGO':
        _, usuario, juego, apuesta_str, resultado = partes
        apuesta = float(apuesta_str)
        gana = (resultado == 'gana')
        if usuario not in users:
            comment('❌ Usuario no existe')
        elif users[usuario].get('bloqueado', False):
            comment('❌ Usuario bloqueado')
        elif users[usuario]['saldoUSDT'] < apuesta:
            comment('❌ Saldo insuficiente')
        else:
            if gana:
                # Determinar ganancia según el juego (simplificado: apuesta * 2 para todos)
                ganancia = apuesta * 2
                users[usuario]['saldoUSDT'] = users[usuario]['saldoUSDT'] - apuesta + ganancia
                comment(f'🎉 {usuario} ganó {ganancia} USDT en {juego}')
            else:
                users[usuario]['saldoUSDT'] -= apuesta
                comment(f'😞 {usuario} perdió {apuesta} USDT en {juego}')
            users[usuario]['movimientos'].append({
                'tipo': f'juego_{juego}',
                'apuesta': apuesta,
                'resultado': 'ganó' if gana else 'perdió',
                'fecha': datetime.now().isoformat()
            })

    # Guardar cambios
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)

if __name__ == '__main__':
    main()
