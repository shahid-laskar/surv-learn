sudo apt update
sudo apt install -y vsftpd

sudo groupadd camftp

# repeat per camera
sudo useradd -m -d /srv/ftp/CAM01 -s /usr/sbin/nologin -G camftp CAM01
sudo passwd CAM01 
/set password

sudo mkdir -p /srv/ftp/CAM01/upload
sudo chown CAM01:camftp /srv/ftp/CAM01/upload
sudo chmod 750 /srv/ftp/CAM01/upload

sudo chown root:root /srv/ftp/CAM01
sudo chmod 755 /srv/ftp/CAM01

Configure /etc/vsftpd.conf
------------------------------------------------------------------
listen=YES
listen_ipv6=NO

anonymous_enable=NO
local_enable=YES
write_enable=YES

chroot_local_user=YES
allow_writeable_chroot=YES

local_umask=022
file_open_mode=0644

# Passive mode
pasv_enable=YES
pasv_min_port=30000
pasv_max_port=30100
pasv_address=10.44.0.209 #change 

# Only allow listed users to log in
userlist_enable=YES
userlist_file=/etc/vsftpd.userlist
userlist_deny=NO

xferlog_enable=YES
xferlog_file=/var/log/vsftpd.log

# LAN only — no TLS needed
ssl_enable=NO
-------------------------------------------------------------------------------
sudo systemctl restart vsftpd
sudo systemctl enable vsftpd
sudo systemctl status vsftpd

echo "/usr/sbin/nologin" | sudo tee -a /etc/shells

sudo usermod -aG camftp your-default-username