package main
import ("fmt"; "net/url")
func main() {
u, _ := url.Parse("rtsp://admin:Bsnl@695033@10.44.0.215:554/stream1")
fmt.Printf("User: %s, Pass: %s\n", u.User.Username(), u.User.Password)
    pwd, _ := u.User.Password()
    fmt.Printf("Parsed Pass: %s\n", pwd)
}
