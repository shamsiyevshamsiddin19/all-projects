class HotelBookingBotError(Exception):
    """Base exception for domain errors."""


class NoRoomsAvailableError(HotelBookingBotError):
    """Raised when there is no available room for the requested dates."""


class InvalidBookingDatesError(HotelBookingBotError):
    """Raised when check-in/check-out dates are invalid."""


class BookingNotCancellableError(HotelBookingBotError):
    """Raised when a booking can no longer be cancelled."""
