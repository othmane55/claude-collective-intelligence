# Demo 2: Real Claude Role Assignment

Bu dizinde çalışan Claude Code instance'ı için özel talimatlar.

## Başlangıç Görevi

Bu Claude instance'ı başladığında:

1. **RabbitMQ'ya bağlan** ve `role.assignments` kuyruğunu dinle
2. **Rol mesajı geldiğinde:**
   - Rolü kabul et
   - `role.acknowledgments` kuyruğuna onay gönder
   - Rolüne göre çalışmaya başla
3. **Rolsüz çalışma:** Rol alana kadar bekle

## Teknik Detaylar

- RabbitMQ: localhost:5672
- Kullanıcı: admin / rabbitmq123
- Dinlenecek kuyruk: `role.assignments`
- Yanıt kuyruğu: `role.acknowledgments`

## Önemli

- Bu bir demo ortamıdır
- Ana Claude (Main Claude) rol ataması yapacak
- Sen (Sub-Claude) rolü alıp onaylayacaksın
