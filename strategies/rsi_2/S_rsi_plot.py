from tradeexecutor.state.visualisation import PlotKind


def plot(state, timestamp, sma_long, sma_short, rsi):
    # Visualize strategy
    # See available Plotly colours here
    # https://community.plotly.com/t/plotly-colours-list/11730/3?u=miohtama
    visualisation = state.visualisation
    visualisation.plot_indicator(
        timestamp,
        "SMA Long",
        PlotKind.technical_indicator_on_price,
        sma_long,
        colour="darkblue",
    )
    visualisation.plot_indicator(
        timestamp,
        "SMA Short",
        PlotKind.technical_indicator_on_price,
        sma_short,
        colour="darkblue",
    )

    visualisation.plot_indicator(
        timestamp,
        "RSI",
        PlotKind.technical_indicator_detached,
        rsi,
        colour="#003300",
    )
    # visualisation.plot_indicator(
    #     timestamp,
    #     "upper",
    #     PlotKind.technical_indicator_overlay_on_detached,
    #     90,
    #     colour="orange",
    #     detached_overlay_name="RSI",
    # )
    # visualisation.plot_indicator(
    #     timestamp,
    #     "lower",
    #     PlotKind.technical_indicator_overlay_on_detached,
    #     10,
    #     colour="orange",
    #     detached_overlay_name="RSI",
    # )
