# ShopHub — Full-Stack E-Commerce Platform

A full-stack e-commerce application built with Django and PostgreSQL, featuring a customer storefront, guest/authenticated shopping cart with automatic merging, and a role-based seller dashboard for inventory and order management.

## Features

- **Custom User model** with role-based access control (Customer / Seller / Admin)
- **Category & Product catalog** with self-referential subcategories and multi-image uploads
- **AJAX-powered storefront** — search, category filtering, price range, and sorting with no page reloads
- **Dual-mode shopping cart** — session-based for guests, persistent for authenticated users, with automatic merge on login
- **Full checkout flow** — order and line-item snapshotting so historical orders are immune to future price/product changes
- **Seller dashboard** — full product CRUD, order management with status workflow (Pending → Shipped → Delivered), sales stats
- **RBAC enforcement** — custom decorators and mixins ensure sellers can only manage their own products and view orders containing their own items
- **Query-optimized throughout** — `select_related` / `prefetch_related` used across all list views to prevent N+1 query issues
- **Production-ready security settings** — HSTS, secure cookies, SSL redirect (auto-enabled when `DEBUG=False`)

## Tech Stack

- **Backend:** Python 3.14, Django 6.0
- **Database:** PostgreSQL
- **Frontend:** Tailwind CSS, vanilla JavaScript (Fetch API)
- **Image handling:** Pillow

## Project Structure

## Project Structure

```
apps/
├── users/       — Custom User model, authentication (signup/login/logout)
├── store/       — Category, Product, ProductImage models + storefront views
├── orders/      — Cart, CartItem, Order, OrderItem models + checkout flow
└── dashboard/   — Seller dashboard, RBAC permissions, product/order CRUD

config/          — Project settings, root URL configuration
templates/       — HTML templates organized by app
```

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL installed and running

### Installation

```bash
git clone <your-repo-url>
cd ecommerce_project

python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### Database setup

```sql
CREATE DATABASE ecommerce_db;
CREATE USER ecommerce_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO ecommerce_admin;

-- PostgreSQL 15+ requires this additional grant:
\c ecommerce_db
GRANT ALL ON SCHEMA public TO ecommerce_admin;
```

### Environment variables

Copy `.env.example` to `.env` and fill in your own values:

```bash
copy .env.example .env      # Windows
# cp .env.example .env        # macOS/Linux
```

### Run migrations and start the server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the storefront, or `http://127.0.0.1:8000/admin/` for the admin panel.

## Key Design Decisions

- **Order/OrderItem snapshotting**: shipping address and product price/name are copied at the moment of purchase rather than referenced live, so historical orders remain accurate even if a user updates their profile or a seller changes prices later.
- **Unified Cart model**: a single `Cart` model with a nullable `user` and `session_key` (rather than separate guest/user cart models) keeps all cart logic in one `CartService` class, avoiding duplicated branching across views.
- **RBAC via decorator + mixin pair**: `seller_required` for function-based views and `SellerRequiredMixin`/`SellerOwnsObjectMixin` for class-based views, ensuring sellers can never access or modify another seller's data even by guessing URLs.

## License

This project was built as a learning exercise and portfolio piece.