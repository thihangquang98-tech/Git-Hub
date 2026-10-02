\# 🦷 Hệ thống Quản lý Phòng khám Nha khoa



Hệ thống quản lý phòng khám nha khoa được xây dựng nhằm hỗ trợ quản lý bệnh nhân, bác sĩ, lịch hẹn, hồ sơ khám bệnh, dịch vụ và hóa đơn.



Hệ thống được triển khai bằng Docker và tích hợp các thành phần giám sát, logging tập trung và bảo mật.



\---



\## 1. Công nghệ sử dụng



\- Python

\- Flask

\- PostgreSQL 16

\- pgAdmin

\- Docker

\- Docker Compose

\- Nginx

\- HTTPS / TLS

\- Prometheus

\- Grafana

\- Loki

\- Promtail

\- cAdvisor

\- PostgreSQL Exporter

\- Git / GitHub



\---



\## 2. Chức năng chính



\### Quản lý bệnh nhân



\- Thêm bệnh nhân

\- Xem danh sách bệnh nhân

\- Cập nhật thông tin bệnh nhân

\- Xóa bệnh nhân



\### Quản lý bác sĩ



\- Quản lý thông tin bác sĩ

\- Quản lý chuyên môn

\- Quản lý lịch làm việc



\### Quản lý lịch hẹn



\- Tạo lịch hẹn

\- Xem lịch hẹn

\- Cập nhật trạng thái lịch hẹn

\- Quản lý lịch khám giữa bác sĩ và bệnh nhân



\### Hồ sơ khám bệnh



\- Lưu thông tin kết quả khám

\- Lưu chẩn đoán

\- Lưu phương pháp điều trị

\- Quản lý lịch sử khám



\### Dịch vụ



\- Quản lý các dịch vụ nha khoa

\- Quản lý giá dịch vụ



\### Hóa đơn



\- Tạo hóa đơn

\- Quản lý chi phí

\- Theo dõi trạng thái thanh toán



\### Phân quyền



Hệ thống có các vai trò:



\- Manager

\- Doctor

\- Receptionist



Mỗi vai trò được giới hạn quyền truy cập theo chức năng.



\---



\## 3. Kiến trúc hệ thống



```text

&#x20;                   Internet / Client

&#x20;                          |

&#x20;                          v

&#x20;                 +------------------+

&#x20;                 |   Nginx HTTPS    |

&#x20;                 |    Port 443      |

&#x20;                 +------------------+

&#x20;                          |

&#x20;                          v

&#x20;                 +------------------+

&#x20;                 |   Flask Web App  |

&#x20;                 |    Port 5000     |

&#x20;                 +------------------+

&#x20;                          |

&#x20;                          v

&#x20;                 +------------------+

&#x20;                 |   PostgreSQL 16  |

&#x20;                 |   Internal 5432  |

&#x20;                 +------------------+



&#x20;      +-------------------+-------------------+

&#x20;      |                   |                   |

&#x20;      v                   v                   v

&#x20;  pgAdmin           PostgreSQL          PostgreSQL

&#x20;                     Exporter             Metrics

&#x20;      |                   |

&#x20;      +-------------------+

&#x20;              |

&#x20;              v

&#x20;         Prometheus

&#x20;              |

&#x20;              v

&#x20;           Grafana





Docker Logs

&#x20;    |

&#x20;    v

&#x20; Promtail

&#x20;    |

&#x20;    v

&#x20;   Loki

&#x20;    |

&#x20;    v

&#x20; Grafana Explore

