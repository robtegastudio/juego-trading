import json
import os
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
        if len(partes) < 3:
            comment('❌ Formato incorrecto. Uso: REGISTER:usuario:contraseña')
        else:
            _, usuario, password = partes
            if usuario in users:
                comment('❌ El usuario ya existe')
            else:
                users[usuario] = usuario_default()
                users[usuario]['password'] = password
                comment(f'✅ Usuario {usuario} registrado correctamente')

    elif tipo == 'TRANSFER':
        if len(partes) < 4:
            comment('❌ Formato incorrecto. Uso: TRANSFER:origen:destino:monto')
        else:
            _, origen, destino, monto_str = partes
            try:
                monto = float(monto_str)
            except:
                comment('❌ Monto inválido')
                return
            if origen not in users:
                comment('❌ Usuario origen no existe')
            elif destino not in users:
                comment('❌ Usuario destino no existe')
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
        if len(partes) < 2:
            comment('❌ Comando admin incompleto')
            return
        accion = partes[1]
        if accion == 'SET_SALDO':
            if len(partes) < 4:
                comment('❌ Uso: ADMIN:SET_SALDO:usuario:monto')
                return
            _, _, objetivo, monto_str = partes
            try:
                monto = float(monto_str)
            except:
                comment('❌ Monto inválido')
                return
            if objetivo in users:
                users[objetivo]['saldoUSDT'] = monto
                comment(f'✅ Saldo de {objetivo} fijado en {monto} USDT')
            else:
                comment('❌ Usuario no existe')
        elif accion == 'BLOQUEAR':
            if len(partes) < 3:
                comment('❌ Uso: ADMIN:BLOQUEAR:usuario')
                return
            _, _, objetivo = partes
            if objetivo in users:
                users[objetivo]['bloqueado'] = True
                comment(f'✅ Usuario {objetivo} bloqueado')
            else:
                comment('❌ Usuario no existe')
        elif accion == 'DESBLOQUEAR':
            if len(partes) < 3:
                comment('❌ Uso: ADMIN:DESBLOQUEAR:usuario')
                return
            _, _, objetivo = partes
            if objetivo in users:
                users[objetivo]['bloqueado'] = False
                comment(f'✅ Usuario {objetivo} desbloqueado')
            else:
                comment('❌ Usuario no existe')
        elif accion == 'SET_PRECIO':
            if len(partes) < 3:
                comment('❌ Uso: ADMIN:SET_PRECIO:precio')
                return
            _, _, precio_str = partes
            try:
                precio = float(precio_str)
            except:
                comment('❌ Precio inválido')
                return
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
            if len(partes) < 4:
                comment('❌ Uso: ADMIN:ENVIAR_TARJETA:usuario:tipo')
                return
            _, _, objetivo, tipo_tarjeta = partes
            if objetivo not in users:
                comment('❌ Usuario no existe')
                return
            import random
            ultimos4 = str(random.randint(1000, 9999))
            cvv = str(random.randint(100, 999))
            mes = str(random.randint(1, 12)).zfill(2)
            anio = str(random.randint(2025, 2030))
            colores = {
                'bronce': ['#cd7f32', '#b06e2b'],
                'plata': ['#c0c0c0', '#a0a0a0'],
                'oro': ['#ffd700', '#daa520'],
                'diamante': ['#b9f2ff', '#87cefa']
            }
            color1, color2 = colores.get(tipo_tarjeta, ['#2a3a5a', '#1e2a3a'])
            tarjeta = {
                'tipo': tipo_tarjeta,
                'ultimos4': ultimos4,
                'cvv': cvv,
                'mes': mes,
                'anio': anio,
                'color1': color1,
                'color2': color2
            }
            users[objetivo]['tarjetas'].append(tarjeta)
            comment(f'✅ Tarjeta {tipo_tarjeta} enviada a {objetivo}')

    elif tipo == 'JUEGO':
        if len(partes) < 5:
            comment('❌ Formato incorrecto. Uso: JUEGO:usuario:juego:apuesta:resultado(gana/pierde)')
            return
        _, usuario, juego, apuesta_str, resultado_str = partes
        try:
            apuesta = float(apuesta_str)
        except:
            comment('❌ Apuesta inválida')
            return
        if usuario not in users:
            comment('❌ Usuario no existe')
            return
        if users[usuario].get('bloqueado', False):
            comment('❌ Usuario bloqueado')
            return
        if users[usuario]['saldoUSDT'] < apuesta:
            comment('❌ Saldo insuficiente')
            return
        if resultado_str == 'gana':
            ganancia = apuesta * 2
            users[usuario]['saldoUSDT'] = users[usuario]['saldoUSDT'] - apuesta + ganancia
            comment(f'🎉 {usuario} ganó {ganancia} USDT en {juego}')
        else:
            users[usuario]['saldoUSDT'] -= apuesta
            comment(f'😞 {usuario} perdió {apuesta} USDT en {juego}')
        users[usuario]['movimientos'].append({
            'tipo': f'juego_{juego}',
            'apuesta': apuesta,
            'resultado': 'ganó' if resultado_str == 'gana' else 'perdió',
            'fecha': datetime.now().isoformat()
        })

    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)

if __name__ == '__main__':
    main()
