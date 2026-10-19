/**
 * Order Validation Middleware
 * Intercepts requests and enforces strict schema validation rules
 * before forwarding to controllers.
 */

const {
    validateListOrdersQuery,
    validateCreateOrderBody,
    validateUpdateOrderBody,
    validateStatusUpdateBody
} = require('../validators/orderValidator');

function validateListQueryMiddleware(req, res, next) {
    try {
        req.validatedQuery = validateListOrdersQuery(req.query);
        next();
    } catch (err) {
        next(err);
    }
}

function validateCreateBodyMiddleware(req, res, next) {
    try {
        req.validatedBody = validateCreateOrderBody(req.body);
        next();
    } catch (err) {
        next(err);
    }
}

function validateUpdateBodyMiddleware(req, res, next) {
    try {
        req.validatedUpdates = validateUpdateOrderBody(req.body);
        next();
    } catch (err) {
        next(err);
    }
}

function validateStatusBodyMiddleware(req, res, next) {
    try {
        req.validatedStatus = validateStatusUpdateBody(req.body);
        next();
    } catch (err) {
        next(err);
    }
}

module.exports = {
    validateListQueryMiddleware,
    validateCreateBodyMiddleware,
    validateUpdateBodyMiddleware,
    validateStatusBodyMiddleware
};
