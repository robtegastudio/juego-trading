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

    # Inicializar estructura para nuevos usuarios
    def usuario_default():
        return {
            'saldoUSDT': 1000,
            'btc': 0,
            'tarjetas': [],
            'movimientos': [],
            'bloqueado': False,
            'rol': 'user'
        }

    # Función para comentar en el issue
    def comment(msg):
        url = f'https://api.github.com/repos/{repo}/issues/{issue_number}/comments'
        headers = {'Authorization': f'token {github_token}'}
        requests.post(url, json={'body': msg}, headers=headers)

    # Procesar según tipo
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
            # Registrar movimiento
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
        # Puedes añadir más comandos: enviar tarjeta, etc.

    elif tipo == 'JUEGO':
        _, usuario, juego, apuesta_str, resultado_str = partes
        apuesta = float(apuesta_str)
        resultado = resultado_str == 'gana'
        if usuario not in users:
            comment('❌ Usuario no existe')
        elif users[usuario].get('bloqueado', False):
            comment('❌ Usuario bloqueado')
        elif users[usuario]['saldoUSDT'] < apuesta:
            comment('❌ Saldo insuficiente')
        else:
            if resultado:
                ganancia = apuesta * 2  # Ejemplo: apuesta duplica
                users[usuario]['saldoUSDT'] += ganancia - apuesta  # ya restamos apuesta?
                # Mejor: restar apuesta y sumar ganancia total
                users[usuario]['saldoUSDT'] = users[usuario]['saldoUSDT'] - apuesta + ganancia
                comment(f'🎉 {usuario} ganó {ganancia} USDT en {juego}')
            else:
                users[usuario]['saldoUSDT'] -= apuesta
                comment(f'😞 {usuario} perdió {apuesta} USDT en {juego}')
            users[usuario]['movimientos'].append({
                'tipo': f'juego_{juego}',
                'apuesta': apuesta,
                'resultado': 'ganó' if resultado else 'perdió',
                'fecha': datetime.now().isoformat()
            })

    # Guardar cambios
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)

if __name__ == '__main__':
    main()
