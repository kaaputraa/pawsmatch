from adoption.models import User, Animal, Appointment
from datetime import date, timedelta
import random

if Animal.objects.count() >= 200:
    print("⚠️ Data sudah tersedia.")
else:
    # --- 1. User section ---
    shelter_admin, _ = User.objects.get_or_create(
        username="shelter_admin",
        defaults={
            "email": "shelter@example.com",
            "password": "admin123",  # Note: this won't hash password!
            "role": "admin",
            "is_staff": True,
            "is_superuser": True
        }
    )

    # Update password (secure hash)
    shelter_admin.set_password("admin123")
    shelter_admin.save()

    user1, _ = User.objects.get_or_create(username="user1", defaults={"email": "user1@example.com", "role": "user"})
    user1.set_password("user123")
    user1.save()

    user2, _ = User.objects.get_or_create(username="user2", defaults={"email": "user2@example.com", "role": "user"})
    user2.set_password("user123")
    user2.save()

    print("✅ 3 user (1 admin, 2 user biasa) disiapkan.")

    # --- 2. Bulk create 200 animals ---
    species_list = ["Dog", "Cat"]
    breed_list = ["Golden Retriever", "Beagle", "Persian", "Siamese", "Bulldog"]
    gender_list = ["Male", "Female"]
    status_choices = ["available", "pending", "adopted"]

    animals = []
    for i in range(200):
        animals.append(Animal(
            name=f"Animal {i+1}",
            species=random.choice(species_list),
            breed=random.choice(breed_list),
            age=random.randint(1, 10),
            gender=random.choice(gender_list),
            description="Hewan penyelamatan butuh rumah.",
            image_url="https://placekitten.com/300/300",
            status=random.choice(status_choices),
            shelter=shelter_admin
        ))

    Animal.objects.bulk_create(animals)
    print("✅ 200 hewan rescue berhasil dibuat.")

    # --- 3. Buat 20 appointment dummy ---
    available_animals = Animal.objects.filter(status="available")[:20]
    for animal in available_animals:
        Appointment.objects.create(
            user=random.choice([user1, user2]),
            animal=animal,
            appointment_date=date.today() + timedelta(days=random.randint(1, 10)),
            status="pending",
            notes="Saya tertarik mengadopsi hewan ini."
        )

    print("✅ 20 appointment dummy dibuat.")
