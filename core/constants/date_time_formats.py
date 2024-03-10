# Datetime formats...

dateTimeFormat = '%Y.%m.%d %H:%M %Z'
dateTagFormat = '%y%m%d-%H%M'  # eg: '220208-0204'
dateTagPreciseFormat = '%y%m%d-%H%M%S'  # eg: '220208-020423'
shortDateFormat = '%Y.%m.%d %H:%M'  # eg: '2022.02.08-02:04'
preciseDateFormat = '%Y.%m.%d %H:%M:%S'  # eg: '2022.02.08-02:04:23'
logDateFormat = '%y%m%d-%H%M%S-%f'  # eg: '220208-020423-255157'
detailedDateFormat = '%Y.%m.%d %H:%M:%S.%f'  # eg: '2022.02.08-02:04:23.255157'


__all__ = [  # Exporting objects...
    'dateTimeFormat',
    'dateTagFormat',
    'dateTagPreciseFormat',
    'shortDateFormat',
    'preciseDateFormat',
    'logDateFormat',
    'detailedDateFormat',
]
