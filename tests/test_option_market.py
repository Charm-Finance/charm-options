from brownie import reverts
import pytest
from pytest import approx


SCALE = 10**18
PERCENT = SCALE // 100
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

CALL = PUT = True
COVER = False


def lslmsr(q, alpha):
    from math import exp, log
    b = alpha * sum(q)
    if b == 0:
        return 0
    mx = max(q)
    a = sum(exp((x-mx)/b) for x in q)
    cost = mx + b * log(a)
    return SCALE * cost


@pytest.mark.parametrize("isEth", [False, True])
@pytest.mark.parametrize("alpha", [1, 10 * PERCENT, SCALE-1])
@pytest.mark.parametrize("isPut", [False, True])
@pytest.mark.parametrize("tradingFee", [0, 10 * PERCENT, SCALE-1])
def test_initialize(a, OptionMarket, MockToken, MockOracle, OptionsToken, isEth, alpha, isPut, tradingFee):
    return # TODO remove

    # setup args
    deployer = a[0]
    baseToken = ZERO_ADDRESS if isEth else deployer.deploy(MockToken)
    oracle = deployer.deploy(MockOracle)
    longTokens = [deployer.deploy(OptionsToken) for _ in range(4)]
    shortTokens = [deployer.deploy(OptionsToken) for _ in range(4)]

    # deploy and initialize
    market = deployer.deploy(OptionMarket)
    market.initialize(
        baseToken,
        oracle,
        longTokens,
        shortTokens,
        [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
        2000000000,  # expiry = 18 May 2033
        alpha,
        isPut,
        tradingFee,
        1000 * SCALE,
        2000 * SCALE,
    )

    # check variables all set
    assert market.baseToken() == baseToken
    assert market.oracle() == oracle
    assert market.expiryTime() == 2000000000
    assert market.alpha() == alpha
    assert market.isPut() == isPut
    assert market.tradingFee() == tradingFee
    assert market.balanceCap() == 1000 * SCALE
    assert market.totalSupplyCap() == 2000 * SCALE

    assert market.maxStrikePrice() == 600
    assert market.numStrikes() == 4

    # check token arrays
    for i in range(4):
        assert market.longTokens(i) == longTokens[i]
    for i in range(4):
        assert market.shortTokens(i) == shortTokens[i]
    with reverts():
        market.longTokens(4)
    with reverts():
        market.shortTokens(4)

    # check strike price array
    for i in range(4):
        assert market.strikePrices(i) == [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE][i]
    with reverts():
        market.strikePrices(4)

    # can't initialize again
    with reverts("Contract instance has already been initialized"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )


@pytest.mark.parametrize("isPut", [False, True])
@pytest.mark.parametrize("isEth", [False, True])
def test_initialize_errors(a, OptionMarket, MockToken, MockOracle, OptionsToken, isPut, isEth):
    return # TODO remove

    # setup args
    deployer = a[0]
    baseToken = ZERO_ADDRESS if isEth else deployer.deploy(MockToken)
    oracle = deployer.deploy(MockOracle)
    longTokens = [deployer.deploy(OptionsToken) for _ in range(4)]
    shortTokens = [deployer.deploy(OptionsToken) for _ in range(4)]

    market = deployer.deploy(OptionMarket)
    with reverts("Alpha must be > 0"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            0,  # alpha = 0
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Alpha must be < 1"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            SCALE,  # alpha = 1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Trading fee must be < 1"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            SCALE,  # tradingFee = 100%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Balance cap must be > 0"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            0,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Total supply cap must be > 0"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            0,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Already expired"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            1500000000,  # expiry = 14 July 2017
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Lengths do not match"):
        market.initialize(
            baseToken,
            oracle,
            longTokens[:3],
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Lengths do not match"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens[:3],
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Strike prices must not be empty"):
        market.initialize(
            baseToken,
            oracle,
            [],
            [],
            [],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Strike prices must be > 0"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [0, 400, 500, 600],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )

    market = deployer.deploy(OptionMarket)
    with reverts("Strike prices must be increasing"):
        market.initialize(
            baseToken,
            oracle,
            longTokens,
            shortTokens,
            [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
            2000000000,  # expiry = 18 May 2033
            1e17,  # alpha = 0.1
            isPut,
            1e16,  # tradingFee = 1%
            1000 * SCALE,
            2000 * SCALE,
        )


def test_buy_and_sell_calls(a, OptionMarket, MockToken, MockOracle, OptionsToken):
    return # TODO remove

    # setup args
    deployer, alice = a[:2]
    baseToken = deployer.deploy(MockToken)
    oracle = deployer.deploy(MockOracle)
    longTokens = [deployer.deploy(OptionsToken) for _ in range(4)]
    shortTokens = [deployer.deploy(OptionsToken) for _ in range(4)]

    # deploy and initialize
    market = deployer.deploy(OptionMarket)
    market.initialize(
        baseToken,
        oracle,
        longTokens,
        shortTokens,
        [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
        2000000000,  # expiry = 18 May 2033
        10 * PERCENT,  # alpha = 0.1
        False,  # call
        1 * PERCENT,  # tradingFee = 1%
        1000 * SCALE,
        2000 * SCALE,
    )
    for token in longTokens + shortTokens:
        token.initialize(market, "name", "symbol", 18)

    # give users base tokens
    baseToken.mint(alice, 100 * SCALE, {"from": deployer})
    baseToken.approve(market, 100 * SCALE, {"from": alice})

    # index out of range
    with reverts("Index too large"):
        tx = market.buy(CALL, 4, SCALE, 100 * SCALE, {"from": alice})
    with reverts("Index too large"):
        tx = market.buy(COVER, 4, SCALE, 100 * SCALE, {"from": alice})

    # can't buy too much
    with reverts("ERC20: transfer amount exceeds balance"):
        market.buy(CALL, 0, 100 * SCALE, 10000 * SCALE, {"from": alice})

    # buy 2 calls
    tx = market.buy(CALL, 0, 2 * SCALE, 100 * SCALE, {"from": alice})
    cost = lslmsr([2, 0, 0, 0, 0], 0.1) + 2 * PERCENT
    assert approx(tx.return_value) == cost
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost
    assert longTokens[0].balanceOf(alice) == 2 * SCALE

    # buy 3 calls
    tx = market.buy(CALL, 2, 3 * SCALE, 100 * SCALE, {"from": alice})
    cost1 = lslmsr([2, 0, 0, 0, 0], 0.1) + 2 * PERCENT
    cost2 = lslmsr([5, 3, 3, 0, 0], 0.1) + 5 * PERCENT
    assert approx(tx.return_value) == cost2 - cost1
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 2 * SCALE
    assert longTokens[2].balanceOf(alice) == 3 * SCALE

    # buy 5 covers
    tx = market.buy(COVER, 3, 5 * SCALE, 100 * SCALE, {"from": alice})
    cost1 = lslmsr([5, 3, 3, 0, 0], 0.1) + 5 * PERCENT
    cost2 = lslmsr([5, 3, 3, 0, 5], 0.1) + 10 * PERCENT
    assert approx(tx.return_value) == cost2 - cost1
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 2 * SCALE
    assert longTokens[2].balanceOf(alice) == 3 * SCALE
    assert shortTokens[3].balanceOf(alice) == 5 * SCALE

    # buy 6 covers
    tx = market.buy(COVER, 0, 6 * SCALE, 100 * SCALE, {"from": alice})
    cost1 = lslmsr([5, 3, 3, 0, 5], 0.1) + 10 * PERCENT
    cost2 = lslmsr([5, 9, 9, 6, 11], 0.1) + 16 * PERCENT
    assert approx(tx.return_value) == cost2 - cost1
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 2 * SCALE
    assert longTokens[2].balanceOf(alice) == 3 * SCALE
    assert shortTokens[0].balanceOf(alice) == 6 * SCALE
    assert shortTokens[3].balanceOf(alice) == 5 * SCALE

    # can't sell more than you have
    with reverts("ERC20: burn amount exceeds balance"):
        market.sell(CALL, 0, 3 * SCALE, 0, {"from": alice})
    with reverts("ERC20: burn amount exceeds balance"):
        market.sell(COVER, 0, 7 * SCALE, 0, {"from": alice})
    with reverts("ERC20: burn amount exceeds balance"):
        market.sell(COVER, 1, 1 * SCALE, 0, {"from": alice})

    # sell 2 covers
    tx = market.sell(COVER, 0, 2 * SCALE, 0, {"from": alice})
    cost1 = lslmsr([5, 9, 9, 6, 11], 0.1) + 16 * PERCENT
    cost2 = lslmsr([5, 7, 7, 4, 9], 0.1) + 18 * PERCENT
    assert approx(tx.return_value) == cost1 - cost2
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 2 * SCALE
    assert longTokens[2].balanceOf(alice) == 3 * SCALE
    assert shortTokens[0].balanceOf(alice) == 4 * SCALE
    assert shortTokens[3].balanceOf(alice) == 5 * SCALE

    # sell 2 calls
    tx = market.sell(CALL, 0, 2 * SCALE, 0, {"from": alice})
    cost1 = lslmsr([5, 7, 7, 4, 9], 0.1) + 18 * PERCENT
    cost2 = lslmsr([3, 7, 7, 4, 9], 0.1) + 20 * PERCENT
    assert approx(tx.return_value) == cost1 - cost2
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 0
    assert longTokens[2].balanceOf(alice) == 3 * SCALE
    assert shortTokens[0].balanceOf(alice) == 4 * SCALE
    assert shortTokens[3].balanceOf(alice) == 5 * SCALE

    # sell 3 calls
    tx = market.sell(CALL, 2, 3 * SCALE, 0, {"from": alice})
    cost1 = lslmsr([3, 7, 7, 4, 9], 0.1) + 20 * PERCENT
    cost2 = lslmsr([0, 4, 4, 4, 9], 0.1) + 23 * PERCENT
    assert approx(tx.return_value) == cost1 - cost2
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 0
    assert longTokens[2].balanceOf(alice) == 0
    assert shortTokens[0].balanceOf(alice) == 4 * SCALE
    assert shortTokens[3].balanceOf(alice) == 5 * SCALE

    # sell 5 covers
    tx = market.sell(COVER, 3, 5 * SCALE, 0, {"from": alice})
    cost1 = lslmsr([0, 4, 4, 4, 9], 0.1) + 23 * PERCENT
    cost2 = lslmsr([0, 4, 4, 4, 4], 0.1) + 28 * PERCENT
    assert approx(tx.return_value) == cost1 - cost2
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 0
    assert longTokens[2].balanceOf(alice) == 0
    assert shortTokens[0].balanceOf(alice) == 4 * SCALE
    assert shortTokens[3].balanceOf(alice) == 0

    # sell 4 covers
    tx = market.sell(COVER, 0, 4 * SCALE, 0, {"from": alice})
    cost1 = lslmsr([0, 4, 4, 4, 4], 0.1) + 28 * PERCENT
    cost2 = 32 * PERCENT
    assert approx(tx.return_value) == cost1 - cost2
    assert approx(baseToken.balanceOf(alice)) == 100 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 0
    assert longTokens[2].balanceOf(alice) == 0
    assert shortTokens[0].balanceOf(alice) == 0
    assert shortTokens[3].balanceOf(alice) == 0


def test_buy_and_sell_puts(a, OptionMarket, MockToken, MockOracle, OptionsToken):

    # setup args
    deployer, alice = a[:2]
    baseToken = deployer.deploy(MockToken)
    oracle = deployer.deploy(MockOracle)
    longTokens = [deployer.deploy(OptionsToken) for _ in range(4)]
    shortTokens = [deployer.deploy(OptionsToken) for _ in range(4)]

    # deploy and initialize
    market = deployer.deploy(OptionMarket)
    market.initialize(
        baseToken,
        oracle,
        longTokens,
        shortTokens,
        [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
        2000000000,  # expiry = 18 May 2033
        10 * PERCENT,  # alpha = 0.1
        True,  # put
        1 * PERCENT,  # tradingFee = 1%
        1000 * SCALE,
        2000 * SCALE,
    )
    for token in longTokens + shortTokens:
        token.initialize(market, "name", "symbol", 18)

    # give users base tokens
    baseToken.mint(alice, 10000 * SCALE, {"from": deployer})
    baseToken.approve(market, 10000 * SCALE, {"from": alice})

    # index out of range
    with reverts("Index too large"):
        tx = market.buy(PUT, 4, SCALE, 100 * SCALE, {"from": alice})
    with reverts("Index too large"):
        tx = market.buy(COVER, 4, SCALE, 100 * SCALE, {"from": alice})

    # can't buy too much
    with reverts("ERC20: transfer amount exceeds balance"):
        market.buy(PUT, 0, 100 * SCALE, 1000000 * SCALE, {"from": alice})

    # buy 2 puts
    tx = market.buy(PUT, 0, 2 * SCALE, 10000 * SCALE, {"from": alice})
    cost = 600 * lslmsr([2, 0, 0, 0, 0], 0.1) + 300 * 2 * PERCENT
    assert approx(tx.return_value) == cost
    assert approx(baseToken.balanceOf(alice)) == 10000 * SCALE - cost
    assert longTokens[0].balanceOf(alice) == 2 * SCALE

    # buy 5 covers
    tx = market.buy(COVER, 2, 5 * SCALE, 10000 * SCALE, {"from": alice})
    cost1 = 600 * lslmsr([2, 0, 0, 0, 0], 0.1) + 300 * 2 * PERCENT
    cost2 = 600 * lslmsr([2, 0, 0, 5, 5], 0.1) + 300 * 2 * PERCENT + 500 * 5 * PERCENT
    assert approx(tx.return_value) == cost2 - cost1
    assert approx(baseToken.balanceOf(alice)) == 10000 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 2 * SCALE
    assert shortTokens[2].balanceOf(alice) == 5 * SCALE

    # can't sell more than you have
    with reverts("ERC20: burn amount exceeds balance"):
        market.sell(CALL, 0, 3 * SCALE, 0, {"from": alice})
    with reverts("ERC20: burn amount exceeds balance"):
        market.sell(COVER, 1, 1 * SCALE, 0, {"from": alice})

    # sell 2 covers
    tx = market.sell(COVER, 2, 2 * SCALE, 0, {"from": alice})
    cost1 = 600 * lslmsr([2, 0, 0, 5, 5], 0.1) + 300 * 2 * PERCENT + 500 * 5 * PERCENT
    cost2 = 600 * lslmsr([2, 0, 0, 3, 3], 0.1) + 300 * 2 * PERCENT + 500 * 7 * PERCENT
    assert approx(tx.return_value) == cost1 - cost2
    assert approx(baseToken.balanceOf(alice)) == 10000 * SCALE - cost2
    assert longTokens[0].balanceOf(alice) == 2 * SCALE
    assert shortTokens[2].balanceOf(alice) == 3 * SCALE


def test_buy_and_sell_with_eth(a, OptionMarket, MockToken, MockOracle, OptionsToken):

    # setup args
    deployer, alice = a[:2]
    oracle = deployer.deploy(MockOracle)
    longTokens = [deployer.deploy(OptionsToken) for _ in range(4)]
    shortTokens = [deployer.deploy(OptionsToken) for _ in range(4)]

    # deploy and initialize
    market = deployer.deploy(OptionMarket)
    market.initialize(
        ZERO_ADDRESS,
        oracle,
        longTokens,
        shortTokens,
        [300 * SCALE, 400 * SCALE, 500 * SCALE, 600 * SCALE],
        2000000000,  # expiry = 18 May 2033
        10 * PERCENT,  # alpha = 0.1
        False,
        1 * PERCENT,  # tradingFee = 1%
        1000 * SCALE,
        2000 * SCALE,
    )
    for token in longTokens + shortTokens:
        token.initialize(market, "name", "symbol", 18)

    # need to send eth with transaction
    with reverts("UniERC20: not enough value"):
        market.buy(CALL, 0, 2 * SCALE, 10000 * SCALE, {"from": alice})
    with reverts("UniERC20: not enough value"):
        market.buy(CALL, 0, 2 * SCALE, 10000 * SCALE, {"from": alice, "value": 1 * SCALE})

    # buy 2 calls
    tx = market.buy(CALL, 0, 2 * SCALE, 100 * SCALE, {"from": alice, "value": 50 * SCALE})
    cost = lslmsr([2, 0, 0, 0, 0], 0.1) + 2 * PERCENT
    assert approx(tx.return_value) == cost
    assert approx(alice.balance()) == 100 * SCALE - cost
    assert longTokens[0].balanceOf(alice) == 2 * SCALE

    # sell 2 calls
    tx = market.sell(CALL, 0, 2 * SCALE, 0, {"from": alice})
    cost = lslmsr([2, 0, 0, 0, 0], 0.1) - 2 * PERCENT
    assert approx(tx.return_value) == cost
    assert approx(alice.balance()) == 100 * SCALE - 4 * PERCENT
    assert longTokens[0].balanceOf(alice) == 0

