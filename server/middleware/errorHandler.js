/**
 * Centralized Error Handling Middleware
 * Provides consistent JSON error responses, maps HTTP status codes,
 * and shields sensitive infrastructure details from external clients.
 */

function errorHandler(err, req, res, next) {
    if (res.headersSent) {
        return next(err);
    }

    // 1. JSON parse errors from body-parser
    if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
        return res.status(400).json({
            success: false,
            error: 'Malformed JSON request body.'
        });
    }

    // 2. Custom status codes
    const statusCode = Number.isInteger(err.statusCode)
        ? err.statusCode
        : (err.status || 500);

    // 3. Log 500+ errors safely
    if (statusCode >= 500) {
        console.error(`Internal server error on ${req.method} ${req.originalUrl}:`, err.message);
    }

    // 4. Client-safe error messages
    if (statusCode === 404) {
        return res.status(404).json({
            success: false,
            message: 'Order not found',
            error: err.message || 'Order not found.'
        });
    }

    let clientMessage;
    if (statusCode === 400 || statusCode === 409 || statusCode === 503) {
        clientMessage = err.message;
    } else {
        clientMessage = 'Internal server error.';
    }

    return res.status(statusCode).json({
        success: false,
        error: clientMessage
    });
}

module.exports = errorHandler;
