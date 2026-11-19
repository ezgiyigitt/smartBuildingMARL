import '../../../../core/widgets/status_page.dart';

class OccupancyForecastingView extends StatusPage {
  const OccupancyForecastingView({super.key})
    : super(
        title: 'Occupancy forecasting',
        body:
            'Forecasts will use CityLearn occupant_count time series with lagged features only. '
            'ASHRAE survey subjects are not building occupants in the simulator.',
      );
}
