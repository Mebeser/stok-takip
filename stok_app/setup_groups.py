from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from stok_app.models import Urun, Musteri, Satis

def setup_groups():
    # 🛠️ **Yönetici Grubu**
    admin_group, created = Group.objects.get_or_create(name="Yönetici")
    if created:
        admin_permissions = Permission.objects.all()  # Tüm yetkileri al
        admin_group.permissions.set(admin_permissions)
        print("✅ Yönetici grubu oluşturuldu ve tüm yetkiler eklendi.")

    # 📦 **Depo Sorumlusu Grubu**
    depo_group, created = Group.objects.get_or_create(name="Depo Sorumlusu")
    if created:
        depo_permissions = Permission.objects.filter(
            content_type__model__in=["urun", "musteri"]
        )
        depo_group.permissions.set(depo_permissions)
        print("✅ Depo sorumlusu grubu oluşturuldu ve yetkiler eklendi.")

    # 🛒 **Satış Sorumlusu Grubu**
    satis_group, created = Group.objects.get_or_create(name="Satış Sorumlusu")
    if created:
        satis_permissions = Permission.objects.filter(
            content_type__model__in=["satis", "musteri"]
        )
        satis_group.permissions.set(satis_permissions)
        print("✅ Satış sorumlusu grubu oluşturuldu ve yetkiler eklendi.")

if __name__ == "__main__":
    setup_groups()


#kullanılacak script kodu 
#python manage.py shell
#>>> exec(open("setup_groups.py").read())