import telebot
import time
import ccxt
import pandas as pd
from flask import Flask
from threading import Thread
from datetime import datetime

# --- CONFIGURATION ---
API_TOKEN = '7961247099:AAH92b0BYBeDHWNfiU8xckcT8qFti1AFeYs'    # 👈 REMETTEZ VOTRE TOKEN
CHAT_ID = '1263674430'         # 👈 REMETTEZ VOTRE CHAT ID
SYMBOL = 'BTC/USD'
TIMEFRAME = '15m'
CAPITAL_FICTIF = 5.0  # On commence avec 5$

# Initialisation
bot = telebot.TeleBot(API_TOKEN)
exchange = ccxt.kraken()
app = Flask('')

# --- MÉMOIRE DU ROBOT ---
trade_en_cours = None  # Stockera les infos du trade actif

# --- SERVEUR UPTIME ---
@app.route('/')
def home():
    return "Bot Simulation Actif"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http_server)
    t.start()

# --- FONCTIONS ---
def obtenir_donnees():
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=50)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        return df
    except:
        return None

def envoyer_msg(texte):
    try:
        bot.send_message(CHAT_ID, texte, parse_mode='HTML')
    except Exception as e:
        print(f"Erreur Telegram: {e}")

# --- CERVEAU PRINCIPAL ---
def analyser_marche():
    global trade_en_cours, CAPITAL_FICTIF
    print("🤖 Mode Simulation Activé...")
    envoyer_msg(f"🤖 <b>BOT ACTIVÉ</b>\nCapital de départ : {CAPITAL_FICTIF} $")

    while True:
        try:
            df = obtenir_donnees()
            
            if df is not None:
                current_price = df.iloc[-1]['close'] # Prix actuel
                
                # --- CAS 1 : UN TRADE EST DÉJÀ EN COURS ---
                if trade_en_cours is not None:
                    type_t = trade_en_cours['type']
                    tp = trade_en_cours['tp']
                    sl = trade_en_cours['sl']
                    entree = trade_en_cours['entree']
                    
                    print(f"⏳ Trade en cours... Prix: {current_price} (TP: {tp} / SL: {sl})")
                    
                    # Vérification GAGNÉ (TP touché)
                    if (type_t == 'ACHAT' and current_price >= tp) or \
                       (type_t == 'VENTE' and current_price <= tp):
                        
                        gain = 3.0 # On gagne 3x la mise (ratio 1:3) supposons mise 1$
                        CAPITAL_FICTIF += gain
                        
                        msg = (f"✅ <b>TRADE GAGNÉ (TP Touché)</b>\n"
                               f"Prix Sortie : {current_price}\n"
                               f"💰 Profit : +{gain} $\n"
                               f"🏦 Nouveau Capital : {CAPITAL_FICTIF} $")
                        envoyer_msg(msg)
                        trade_en_cours = None # On vide la mémoire, prêt pour le prochain

                    # Vérification PERDU (SL touché)
                    elif (type_t == 'ACHAT' and current_price <= sl) or \
                         (type_t == 'VENTE' and current_price >= sl):
                        
                        perte = 1.0 # On perd 1$
                        CAPITAL_FICTIF -= perte
                        
                        msg = (f"❌ <b>TRADE PERDU (SL Touché)</b>\n"
                               f"Prix Sortie : {current_price}\n"
                               f"💸 Perte : -{perte} $\n"
                               f"🏦 Nouveau Capital : {CAPITAL_FICTIF} $")
                        envoyer_msg(msg)
                        trade_en_cours = None

                # --- CAS 2 : PAS DE TRADE, ON CHERCHE UN SIGNAL ---
                else:
                    impulsion = df.iloc[-2] # Avant-dernière bougie
                    ob_candle = df.iloc[-3] # Bougie d'avant
                    
                    body_imp = abs(impulsion['close'] - impulsion['open'])
                    moyenne = (abs(df['close'] - df['open']).rolling(window=20).mean()).iloc[-2]
                    
                    # SI SIGNAL DÉTECTÉ (Impulsion > 2x Moyenne)
                    if body_imp > (moyenne * 2):
                        
                        signal_trouve = False
                        
                        # Achat
                        if impulsion['close'] > impulsion['open']:
                            signal_type = 'ACHAT'
                            entree = ob_candle['high']
                            sl = ob_candle['low']
                            risque = entree - sl
                            tp = entree + (risque * 3)
                            signal_trouve = True
                        
                        # Vente
                        elif impulsion['close'] < impulsion['open']:
                            signal_type = 'VENTE'
                            entree = ob_candle['low']
                            sl = ob_candle['high']
                            risque = sl - entree
                            tp = entree - (risque * 3)
                            signal_trouve = True
                        
                        # SI SIGNAL VALIDÉ -> ON LANCE LA SIMULATION
                        if signal_trouve:
                            trade_en_cours = {
                                'type': signal_type,
                                'entree': entree,
                                'sl': sl,
                                'tp': tp,
                                'heure': datetime.now().strftime("%H:%M")
                            }
                            
                            msg = (f"🚀 <b>NOUVEAU TRADE SIMULÉ</b>\n"
                                   f"Type : {signal_type}\n"
                                   f"Entrée : {entree}\n"
                                   f"Stop Loss : {sl}\n"
                                   f"Take Profit : {tp}")
                            envoyer_msg(msg)
                            print(">>> NOUVEAU TRADE LANCÉ <<<")
                    
                    else:
                        print(f"👀 Scan... Prix: {current_price} | Capital: {CAPITAL_FICTIF}$")

            time.sleep(15) # Pause 15 sec
            
        except Exception as e:
            print(f"Erreur: {e}")
            time.sleep(5)

if __name__ == '__main__':
    keep_alive()
    analyser_marche()
