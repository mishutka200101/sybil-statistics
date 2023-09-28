import asyncio
from aiohttp import ClientSession

from .helper import get_eth_price, parse_tokens, parse_transactions


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


async def run_workers(addresses: list, session=ClientSession()):
    """
    Запускает асинхронные задачи для получения данных о токенах и транзакциях для нескольких адресов одновременно.

    Args:
        addresses (list): Список адресов для запроса данных.

    Returns:
        list: Список данных о токенах и транзакциях для всех адресов.
    """
    tasks_tokens = []
    tasks_transactions = []

    for address in addresses:
        tasks_tokens.append(asyncio.ensure_future(
            get_tokens(session=session, address=address)))
        tasks_transactions.append(asyncio.ensure_future(
            get_transactions(session=session, address=address)))

    tokens = await asyncio.gather(*tasks_tokens)
    transactions = await asyncio.gather(*tasks_transactions)

    # task_transfers = []
    #
    # for transaction in transactions:
    #     task_transfers.append(asyncio.ensure_future(get_transfers(session=session, transaction_id=transaction['hash'])))
    #
    # transfers = await asyncio.gather(*task_transfers)

    await session.close()
    return tokens, transactions


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
        txs, bridge_count, syncswap_count, maverick_count, izumi_count, spacefi_count, merkly_count = parse_transactions(
            transactions[i])

        ETH = round(ETH * eth_price, 2)

        result_list.append(
            [address, ETH, USDC, USDT, txs, bridge_count, syncswap_count,
                maverick_count, izumi_count, spacefi_count, merkly_count]
        )

    return result_list
