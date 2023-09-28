import requests


def get_eth_price():
    try:
        res = requests.get(
            url='https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USDT')
        return float(res.json()["USDT"])
    except Exception:
        return 0


def parse_transactions(transactions: list):
    """
    Обрабатывает список транзакций и возвращает статистику по адресам получателей.

    Args:
        transactions (list): Список транзакций.

    Returns:
        list: Список статистики, включая общее количество транзакций и количество транзакций для каждого адреса получателя.
    """
    SYNCSWAP = '0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295'
    WOOFI = '0xfd505702b37Ae9b626952Eb2DD736d9045876417'
    MAVERICK = '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4'
    IZUMI = '0x943ac2310D9BC703d6AB5e5e76876e212100f894'
    SPACEFI = '0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d'
    MERKLY = '0x5673B6e6e51dE3479B8deB22dF46B12308db5E1e'

    # BRIDGE = ['0x80C67432656d59144cEFf962E8fAF8926599bCF8',
    #           '0xE4eDb277e41dc89aB076a1F049f4a3EfA700bCE8']

    txs, syncswap_count, woofi_count, maverick_count, izumi_count, spacefi_count, merkly_count = 0, 0, 0, 0, 0, 0, 0

    if transactions:
        for transaction in transactions:
            statuses = ['verified', 'committed', 'proved']
            if transaction['status'] in statuses:
                txs += 1
                to = transaction['to']
                _from = transaction['from']

                # if _from in BRIDGE:
                #     bridge_count = 1

                if to == SYNCSWAP:
                    syncswap_count += 1
                elif to == WOOFI:
                    woofi_count += 1
                elif to == MAVERICK:
                    maverick_count += 1
                elif to == IZUMI:
                    izumi_count += 1
                elif to == SPACEFI:
                    spacefi_count += 1
                elif to == MERKLY:
                    merkly_count += 1

    result = [
        txs,
        syncswap_count,
        woofi_count,
        maverick_count,
        izumi_count,
        spacefi_count,
        merkly_count
    ]

    return result


def parse_tokens(tokens: dict):
    """
    Обрабатывает словарь токенов и возвращает балансы для ETH, USDC и USDT.

    Args:
        tokens (dict): Словарь токенов.

    Returns:
        list: Список балансов ETH, USDC и USDT.
    """
    def dec_to_int(balance: int, decimals: int):
        return balance / 10 ** decimals

    ETH = 0
    USDC = 0
    USDT = 0

    if tokens:
        for _ in tokens.keys():
            token = tokens[_]
            balance = dec_to_int(balance=int(
                token['balance']), decimals=int(token['token']['decimals']))
            symbol = token['token']['symbol']

            if symbol == 'ETH':
                ETH = balance
            elif symbol == 'USDC':
                USDC = balance
            elif symbol == 'USDT':
                USDT = balance

    return ETH, USDC, USDT
