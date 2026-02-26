class ErrorMessages:
  # Generic 400 error
  RESOURCE_NOT_FOUND = "Resource not found."

  # Auth errors
  UNAUTHORIZED = "Incorrect username or password."
  INVALID_CREDENTIALS = "Could not validate credentials"
  NOT_ENOUGH_PERMISSIONS = "You don't have enough permissions to perform this action."
  NOT_ENOUGH_PERMISSIONS_UPDATE_ROLE = "You don't have enough permissions to update the user role."
  DELETED_USER = "The user was deleted."

  # Unhandled errors
  INTEGRITY_ERROR = "Data integrity conflict (possible duplicate record)."
  UNEXPECTED_ERROR = "An unexpected error has occurred on the server."

  # User errors
  SHORT_PASSWORD = "The password must contain at least 8 characters."
  SHORT_NAME = "The name must contain at least 3 characters, not counting extra blank spaces."
  PASSWORDS_MISMATCH = "The passwords don't match."
  DUPLICATED_USERNAME = "The user already exists."
  USER_NOT_FOUND = "User not found."
  INACTIVE_USER = "The user account is inactive."
  EMPTY_NAME = "The name cannot be empty."
  USER_ALREADY_ACTIVE = "The user is already active."
  DELETE_CURRENT_ADMIN = "You cannot delete yourself as admin through this endpoint; use the DELETE '/users/me' endpoint instead."
  CANNOT_RESTORE_ADMIN = "Only super admins can restore admin accounts."
  CANNOT_DELETE_ADMIN = "Only super admins can delete admin accounts."
  CANNOT_UPDATE = "Only super admins can update admin accounts."
  CANNOT_DOWNGRADE_LAST_SUPERADMIN = "You cannot downgrade the last super admin."
  CANNOT_UPDATE_ADMIN = "Only super admins can update admin accounts."
  DELETE_LAST_SUPERADMIN = "You cannot delete the last super admin."
  DISABLE_LAST_SUPERADMIN = "You can't disable the last super admin."

  # Hall errors
  DUPLICATED_HALL_NAME = "There's already a hall with that name."
  HALL_NOT_FOUND = "Hall not found."
  UNAVAILABLE_HALL = "The hall isn't available in this moment."
  DELETED_HALL = "It appears the hall was deleted."

  # Reservation errors
  INVALID_DATE = "The date is invalid; it must be at least one day after the current date."
  DUPLICATED_RESERVATION = "There's already a reservation for that hall on that date."
  RESERVATION_NOT_FOUND = "Reservation not found."
  RESERVATION_USER_CONFLICT = "The reservation is not from this user."
  INVALID_STATUS = "Invalid status."
  INVALID_TRANSITION = "Invalid status transition."
  INVALID_FINALIZATION = "The reservation cannot be finalized because today is not the reservation date."
  RESERVATION_FROM_OTHER_USER = "You are not the owner of this reservation and you do not have permission to access it."
