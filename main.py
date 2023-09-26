from aiohttp import ClientSession
import asyncio
import requests
import streamlit as st
import pandas as pd


def get_eth_price():
    try:
        res = requests.get(url='https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USDT')
        return float(res.json()["USDT"])
    except Exception:
        return 0


def create_session() -> ClientSession:
    """
    Создает и возвращает сессию клиента для выполнения HTTP-запросов.

    Returns:
        aiohttp.ClientSession: Сессия клиента.
    """
    # headers = {
    #     # Здесь находятся ваши заголовки
    # }
    return ClientSession()


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

    BRIDGE = ['0x80C67432656d59144cEFf962E8fAF8926599bCF8', '0xE4eDb277e41dc89aB076a1F049f4a3EfA700bCE8']

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
            balance = dec_to_int(balance=int(token['balance']), decimals=int(token['token']['decimals']))
            symbol = token['token']['symbol']

            if symbol == 'ETH':
                ETH = balance
            elif symbol == 'USDC':
                USDC = balance
            elif symbol == 'USDT':
                USDT = balance

    return [ETH, USDC, USDT]


async def get_transfers(session: ClientSession, transaction_id: str):
    try:
        async with session.get(url=f'https://block-explorer-api.mainnet.zksync.io/transactions/{transaction_id}/transfers?limit=100&page=1') as res:
            res_json = await res.json()
            return res_json.get('items', None)
    except Exception:
        pass


async def get_tokens(session: ClientSession, address: str):
    """
    Асинхронно получает данные о токенах для указанного адреса.

    Args:
        session (aiohttp.ClientSession): Сессия клиента.
        address (str): Адрес для запроса данных.

    Returns:
        list: Список данных о токенах для адреса.
    """
    try:
        async with session.get(url=f'https://block-explorer-api.mainnet.zksync.io/address/{address}') as res:
            res_json = await res.json()
            return res_json.get('balances', None)
    except Exception as e:
        print(f"Failed to fetch tokens for address {address}: {str(e)}")


async def get_transactions(session: ClientSession, address: str):
    """
    Асинхронно получает данные о транзакциях для указанного адреса.

    Args:
        session (aiohttp.ClientSession): Сессия клиента.
        address (str): Адрес для запроса данных.

    Returns:
        list: Список данных о транзакциях для адреса.
    """
    params = {
        'address': address,
        'limit': 100,
        'page': 1
    }

    try:
        async with session.get(url=f'https://block-explorer-api.mainnet.zksync.io/transactions', params=params) as res:
            res_json = await res.json()
            return res_json.get('items', None)
    except Exception as e:
        print(f"Failed to fetch transactions for address {address}: {str(e)}")


async def run_workers(addresses: list):
    """
    Запускает асинхронные задачи для получения данных о токенах и транзакциях для нескольких адресов одновременно.

    Args:
        addresses (list): Список адресов для запроса данных.

    Returns:
        list: Список данных о токенах и транзакциях для всех адресов.
    """
    session = create_session()

    tasks_tokens = []
    tasks_transactions = []

    for address in addresses:
        tasks_tokens.append(asyncio.ensure_future(get_tokens(session=session, address=address)))
        tasks_transactions.append(asyncio.ensure_future(get_transactions(session=session, address=address)))

    tokens = await asyncio.gather(*tasks_tokens)
    transactions = await asyncio.gather(*tasks_transactions)

    # task_transfers = []
    #
    # for transaction in transactions:
    #     task_transfers.append(asyncio.ensure_future(get_transfers(session=session, transaction_id=transaction['hash'])))
    #
    # transfers = await asyncio.gather(*task_transfers)

    await session.close()
    return [tokens, transactions]


def run_all(addresses: list) -> list:
    """
    Выполняет асинхронно получение и обработку данных о токенах и транзакциях для списка адресов.

    Args:
        addresses (list): Список адресов для запроса данных.

    Returns:
        list: Список результатов обработки данных для каждого адреса.
    """
    tokens, transactions = asyncio.run(run_workers(addresses=addresses))

    result_list = []

    eth_price = get_eth_price()

    for i, address in enumerate(addresses):
        ETH, USDC, USDT = parse_tokens(tokens[i])
        txs, bridge_count, syncswap_count, maverick_count, izumi_count, spacefi_count, merkly_count = parse_transactions(transactions[i])

        ETH = round(ETH * eth_price, 2)

        result_list.append(
            [address, ETH, USDC, USDT, txs, bridge_count, syncswap_count, maverick_count, izumi_count, spacefi_count, merkly_count]
        )

    return result_list


st.set_page_config(page_title="ZkSync Sybil")
st.title("ZkSync Sybil")

addresses_str = st.text_area(label='Insert addresses that splitted by ENTER')
addresses = addresses_str.split('\n')
addresses_stripped = [_.strip() for _ in addresses][:1000]

if not addresses_str:
    st.stop()

try:
    data = run_all(addresses=addresses_stripped)
    columns = [
        'address',
        'ETH in USD',
        'USDC',
        'USDT',
        'txs',
        'SyncSwap',
        'Woofi',
        'Maverick',
        'Izumi',
        'SpaceFi',
        'Merkly'
    ]
    df = pd.DataFrame(data=data, columns=columns)
    df.index += 1
    st.dataframe(data=df, use_container_width=True)

    eth_value = sum(df["ETH in USD"])
    usdt_value = sum(df["USDT"])
    usdc_value = sum(df["USDC"])
    total_sum = eth_value + usdt_value + usdc_value
    st.title(f"Total balance is: {round(total_sum, 2)}$")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
