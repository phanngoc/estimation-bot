# Manufacturing API Documentation

## 1. Production Order API
- `POST /api/production-orders` - Create new production order (8h)
- `GET /api/production-orders` - Get list of production orders (8h)
- `GET /api/production-orders/{id}` - Get production order details (12h)
- `PUT /api/production-orders/{id}` - Update production order (12h)
- `DELETE /api/production-orders/{id}` - Delete production order (8h)

## 2. Material Management API
- `GET /api/materials` - Get list of materials (12h)
- `POST /api/materials` - Add new material (16h)
- `GET /api/materials/{id}` - Get material details (8h)
- `PUT /api/materials/{id}` - Update material information (12h)
- `DELETE /api/materials/{id}` - Delete material (8h)

## 3. Machine Management API
- `GET /api/machines` - Get list of machines (8h)
- `POST /api/machines` - Add new machine (12h)
- `GET /api/machines/{id}` - Get machine details (8h)
- `PUT /api/machines/{id}` - Update machine status (12h)
- `DELETE /api/machines/{id}` - Delete machine (8h)

## 4. Worker Management API
- `GET /api/workers` - Get list of workers (8h)
- `POST /api/workers` - Add new worker (12h)
- `GET /api/workers/{id}` - Get worker details (8h)
- `PUT /api/workers/{id}` - Update worker information (12h)
- `DELETE /api/workers/{id}` - Delete worker (8h)

## 5. Production Confirmation API
- `POST /api/production-confirmations` - Confirm production progress (12h)
- `GET /api/production-confirmations` - Get list of production confirmations (8h)
- `GET /api/production-confirmations/{id}` - Get confirmation details (8h)
- `PUT /api/production-confirmations/{id}` - Update production confirmation (12h)
- `DELETE /api/production-confirmations/{id}` - Delete production confirmation (8h)

## 6. Quality Check API
- `POST /api/quality-checks` - Create quality check report (12h)
- `GET /api/quality-checks` - Get list of quality checks (8h)
- `GET /api/quality-checks/{id}` - Get quality check details (8h)
- `PUT /api/quality-checks/{id}` - Update quality check (12h)
- `DELETE /api/quality-checks/{id}` - Delete quality check (8h)

## 7. Production History API
- `GET /api/production-history` - Get production history (12h)
- `GET /api/production-history/{orderId}` - Get production history by order ID (8h)

Total sum all est time: 316 hours
