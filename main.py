from aiohttp import ClientSession
import asyncio
import streamlit as st
import pandas as pd


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
    contracts = {
        '0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295': 'SyncSwap',
        '0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4': 'Maverick',
        '0x943ac2310D9BC703d6AB5e5e76876e212100f894': 'Izumi',
        '0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d': 'SpaceFi',
        '0x5673B6e6e51dE3479B8deB22dF46B12308db5E1e': 'Merkly'
    }

    txs = len(transactions)
    counts = {contract: 0 for contract in contracts.values()}

    for transaction in transactions:
        if transaction['status'] == 'verified':
            to = transaction['to']
            if to in addresses:
                counts[contracts[to]] += 1

    return [txs] + list(counts.values())


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

    ETH, USDC, USDT = 0, 0, 0

    for token in tokens.values():
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
    for _ in range(5):
        try:
            async with session.get(url=f'https://block-explorer-api.mainnet.zksync.io/transactions/{transaction_id}/transfers?limit=100&page=1') as res:
                res_json = await res.json()
                return res_json['items']
        except Exception:
            pass
    return None


async def get_tokens(session: ClientSession, address: str):
    """
    Асинхронно получает данные о токенах для указанного адреса.

    Args:
        session (aiohttp.ClientSession): Сессия клиента.
        address (str): Адрес для запроса данных.

    Returns:
        list: Список данных о токенах для адреса.
    """
    for _ in range(5):
        try:
            async with session.get(url=f'https://block-explorer-api.mainnet.zksync.io/address/{address}') as res:
                res_json = await res.json()
                return res_json['balances']
        except Exception as e:
            print(f"Failed to fetch tokens for address {address}: {str(e)}")
    return None


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

    for _ in range(5):
        try:
            async with session.get(url=f'https://block-explorer-api.mainnet.zksync.io/transactions', params=params) as res:
                res_json = await res.json()
                return res_json['items']
        except Exception as e:
            print(f"Failed to fetch transactions for address {address}: {str(e)}")
    return None


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

    # for transaction in transactions:
    #     task_transfers.append(
    #         asyncio.ensure_future(get_transfers(session=session, transaction_id=transaction['hash'])))
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

    for i, address in enumerate(addresses):
        ETH, USDC, USDT = parse_tokens(tokens[i])
        txs, syncswap_count, maverick_count, izumi_count, spacefi_count, merkly_count = parse_transactions(
            transactions[i])

        result_list.append(
            [address, ETH, USDC, USDT, txs, syncswap_count, maverick_count, izumi_count, spacefi_count,
             merkly_count]
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
        'ETH',
        'USDC',
        'USDT',
        'txs',
        'SyncSwap',
        'Maverick',
        'Izumi',
        'SpaceFi',
        'Merkly'
    ]
    df = pd.DataFrame(data=data, columns=columns)
    df.index += 1
    st.dataframe(data=df, use_container_width=True)
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
